// Offline checks: the panel helpers, and plugin.js driven through a stand-in
// Penpot API. The real Penpot runs are test/e2e_run.py and test/e2e_more.py.
//
//   npm run build && node test/run.js

const fs = require('fs')
const path = require('path')
const vm = require('vm')

const ROOT = path.join(__dirname, '..')
let passed = 0
let failed = 0

function check(name, ok, detail) {
    if (ok) {
        passed += 1
        console.log('  ok   ' + name)
    } else {
        failed += 1
        console.log('  FAIL ' + name + (detail ? '  ' + detail : ''))
    }
}

// ---------------------------------------------------------------- helpers

function loadLib() {
    const html = fs.readFileSync(path.join(ROOT, 'public', 'index.html'), 'utf8')
    const code = html.match(/<script id="asyntai-lib">([\s\S]*?)<\/script>/)[1]
    const sandbox = { module: { exports: {} } }
    vm.createContext(sandbox)
    vm.runInContext(code, sandbox)
    return sandbox.module.exports
}

const lib = loadLib()
console.log('panel helpers')

check('truncate keeps short text', lib.truncate('  Hi   there ', 20) === 'Hi there')
check('truncate cuts with an ellipsis', lib.truncate('abcdefghij', 5) === 'abcd…')
check('questionKey drops accents and case', lib.questionKey('Kolik to STOJÍ?') === 'kolik to stoji')
check('questionKey drops punctuation', lib.questionKey('Price, please!!') === 'price please')
check('pagePath keeps the path', lib.pagePath('https://shop.example.com/cart/?a=1') === '/cart')
check('pagePath keeps the root', lib.pagePath('https://shop.example.com') === '/')
check('pagePath ignores inbox addresses', lib.pagePath('api://gmail_1234') === '')
check('a lead marker is not a question', !lib.isRealQuestion('[EMAIL_SUBMITTED] a@b.co'))
check('an email address is not a question', !lib.isRealQuestion('write to me at a.b@example.com'))
check('a phone number is not a question', !lib.isRealQuestion('call +420 777 123 456 please'))
check('"hello" is not a question', !lib.isRealQuestion('hello'))
check('"Pricing?" is a question', lib.isRealQuestion('Pricing?'))
check('a real sentence is a question', lib.isRealQuestion('Do you ship to Austria?'))

const sessions = [
    { first_message: 'Do you ship to Austria?', page_url: 'https://shop.example.com/shipping/', country: 'Austria', category: '' },
    { first_message: 'do you ship to austria', page_url: 'https://shop.example.com/', country: '', category: '' },
    { first_message: 'Where is my order?', page_url: 'https://shop.example.com/orders', country: 'Czechia', category: 'Orders' },
    { first_message: '[PHONE_SUBMITTED] +420 777 123 456', page_url: '', country: '', category: '' },
    { first_message: 'hi', page_url: '', country: '', category: '' },
]
const groups = lib.groupQuestions(sessions, 10)
check('the same question in other words is one card', groups.length === 2, JSON.stringify(groups))
check('the most asked question comes first', groups[0].question === 'Do you ship to Austria?')
check('the meta line counts and names the page', groups[0].meta === 'asked 2 times  ·  /shipping  ·  Austria', groups[0].meta)
check('a single question shows page, country and topic', groups[1].meta === '/orders  ·  Czechia  ·  Orders', groups[1].meta)
check('the limit is kept', lib.groupQuestions(sessions, 1).length === 1)
check('sinceIso counts back in days', lib.sinceIso(7, '2026-09-25T10:00:00Z') === '2026-09-18')
check('sinceIso is empty for all time', lib.sinceIso(0) === '')
check('boardTitle names the period', lib.boardTitle(30) === 'Visitor questions, last 30 days')
check('boardTitle for all time', lib.boardTitle(0) === 'Visitor questions')
check('theme read from the hash Penpot uses', lib.themeFromQuery('#/?theme=dark') === 'dark')
check('theme defaults to light', lib.themeFromQuery('') === 'light')

// real-sessions.json is a scrubbed copy of real chats that stays on the
// developer's machine. The public repository has only the made-up shop.
const realPath = path.join(__dirname, 'real-sessions.json')
const real = JSON.parse(fs.readFileSync(fs.existsSync(realPath) ? realPath : path.join(__dirname, 'demo-sessions.json'), 'utf8'))
const realGroups = lib.groupQuestions(real, 100)
const leaks = realGroups.filter((g) => /[\w.+-]+@[\w-]+\.[\w.]+/.test(g.question + g.meta))
check('chat data: no email address reaches a card', leaks.length === 0, JSON.stringify(leaks[0]))
check('chat data: no marker row reaches a card', !realGroups.some((g) => /^\s*\[[A-Z_]{3,}\]/.test(g.question)))

// ---------------------------------------------------------------- fake Penpot

let nextId = 1

function makeShape(type, extra) {
    const shape = Object.assign({
        id: 'shape-' + nextId++,
        type: type,
        name: type === 'board' ? 'Board' : 'Text',
        parent: null,
        x: 0,
        y: 0,
        width: 100,
        height: 100,
        fills: [],
        opacity: 1,
        borderRadius: 0,
        layoutChild: undefined,
        resize(w, h) { this.width = w; this.height = h },
    }, extra || {})
    return shape
}

function makeBoard(root) {
    const board = makeShape('board', {
        children: [],
        clipContent: true,
        flex: undefined,
        appendChild(child) {
            if (child.parent && child.parent.children) {
                child.parent.children = child.parent.children.filter((c) => c !== child)
            }
            child.parent = this
            this.children.push(child)
            if (this.flex) {
                child.layoutChild = { horizontalSizing: 'auto', verticalSizing: 'auto' }
            }
        },
        addFlexLayout() {
            const board = this
            this.flex = {
                dir: 'row', rowGap: 0, columnGap: 0,
                topPadding: 0, rightPadding: 0, bottomPadding: 0, leftPadding: 0,
                appendChild(child) { board.appendChild(child) },
            }
            return this.flex
        },
    })
    if (root) {
        root.appendChild(board)
    }
    return board
}

function makePenpot() {
    const store = {}
    const root = makeBoard(null)
    root.name = 'Root Frame'
    const page = {
        id: 'page-1',
        root: root,
        findShapes() {
            const out = []
            const walk = (node) => {
                for (const child of node.children || []) {
                    out.push(child)
                    walk(child)
                }
            }
            walk(root)
            return out
        },
    }
    const toUi = []
    let onMessage = null
    const penpot = {
        theme: 'dark',
        currentPage: page,
        selection: [],
        opened: null,
        closed: false,
        resized: null,
        zoomed: null,
        listeners: {},
        ui: {
            open(name, url, options) { penpot.opened = { name, url, options } },
            sendMessage(message) { toUi.push(message) },
            onMessage(callback) { onMessage = callback },
            resize(w, h) { penpot.resized = [w, h] },
        },
        on(type, callback) { penpot.listeners[type] = callback; return Symbol(type) },
        localStorage: {
            getItem(key) { return Object.prototype.hasOwnProperty.call(store, key) ? store[key] : null },
            setItem(key, value) { store[key] = String(value) },
            removeItem(key) { delete store[key] },
            getKeys() { return Object.keys(store) },
        },
        viewport: { zoomIntoView(shapes) { penpot.zoomed = shapes } },
        createBoard() { return makeBoard(root) },
        createText(characters) {
            const text = makeShape('text', { characters: characters, growType: 'fixed', fontSize: '14', fontWeight: '400' })
            root.appendChild(text)
            return text
        },
        closePlugin() { penpot.closed = true },
    }
    return {
        penpot: penpot,
        store: store,
        root: root,
        toUi: toUi,
        send(message) { onMessage(message) },
    }
}

function runPlugin() {
    const fake = makePenpot()
    const code = fs.readFileSync(path.join(ROOT, 'public', 'plugin.js'), 'utf8')
    const sandbox = { penpot: fake.penpot, console: console }
    vm.createContext(sandbox)
    vm.runInContext(code, sandbox)
    return fake
}

console.log('\nplugin.js in a stand-in Penpot')

const items = []
for (let i = 0; i < 7; i++) {
    items.push({ question: 'Question number ' + (i + 1) + '?', meta: i === 3 ? '' : 'asked ' + (7 - i) + ' times' })
}

let fake = runPlugin()
check('the panel opens with the plugin name', fake.penpot.opened && fake.penpot.opened.name === 'Customer Questions by Asyntai')
check('the panel gets the Penpot theme', fake.penpot.opened.url === '?theme=dark', fake.penpot.opened.url)
check('the panel is 360 wide', fake.penpot.opened.options.width === 360)
check('the plugin follows theme changes', typeof fake.penpot.listeners.themechange === 'function')
fake.penpot.listeners.themechange('light')
check('a theme change reaches the panel', fake.toUi.some((m) => m.type === 'theme' && m.theme === 'light'))

fake.send({ type: 'ready' })
let init = fake.toUi.filter((m) => m.type === 'init').pop()
check('ready answers init with no key at first', init && init.apiKey === '', JSON.stringify(init))

fake.send({ type: 'save-key', apiKey: 'asy_test_123' })
check('save-key stores the key', fake.store['asyntai-api-key'] === 'asy_test_123')
fake.send({ type: 'ready' })
init = fake.toUi.filter((m) => m.type === 'init').pop()
check('ready hands the stored key back', init.apiKey === 'asy_test_123')
fake.send({ type: 'forget-key' })
check('forget-key removes the key', !('asyntai-api-key' in fake.store))

fake.send({ type: 'resize', height: 5000 })
check('resize is capped at 720', fake.penpot.resized[1] === 720)
fake.send({ type: 'resize', height: 10 })
check('resize is at least 240', fake.penpot.resized[1] === 240)

fake.send({ type: 'insert', title: 'Visitor questions, last 30 days', items: [] })
check('an empty insert is refused', fake.toUi.some((m) => m.type === 'error' && /nothing to add/.test(m.message)))

fake.send({ type: 'insert', title: 'Visitor questions, last 30 days', items: items })
const done = fake.toUi.filter((m) => m.type === 'inserted').pop()
check('insert reports the count', done && done.count === 7, JSON.stringify(done))

const blocks = fake.root.children.filter((c) => c.type === 'board')
check('one block on the page', blocks.length === 1, String(blocks.length))
const block = blocks[0]
check('the block is named after the period', block.name === 'Visitor questions, last 30 days')
check('the block is 5 cards wide', block.width === 80 * 2 + 5 * 280 - 40, String(block.width))
check('the block is 2 rows high', block.height === 80 * 2 + 140 + 2 * 280 - 40, String(block.height))
check('the block does not clip', block.clipContent === false)
const title = block.children.find((c) => c.type === 'text')
check('the title sits at the padding', title && title.x === 80 && title.y === 80)
check('the title is named Title', title.name === 'Title')
const cards = block.children.filter((c) => c.type === 'board')
check('one card per question', cards.length === 7)
check('card 1 sits at the first cell', cards[0].x === 80 && cards[0].y === 220, cards[0].x + ',' + cards[0].y)
check('card 6 wraps to the second row', cards[5].x === 80 && cards[5].y === 500, cards[5].x + ',' + cards[5].y)
check('card 3 sits in the third column', cards[2].x === 640, String(cards[2].x))
check('cards are 240 square', cards.every((c) => c.width === 240 && c.height === 240))
check('cards are a flex column', cards.every((c) => c.flex && c.flex.dir === 'column'))
check('cards are grey with round corners', cards.every((c) => c.fills[0].fillColor === '#F2F2F2' && c.borderRadius === 8))
const first = cards[0].children
check('question is appended last so it shows first', first[first.length - 1].name === 'Question' && first[0].name === 'Details')
check('question text is the question', first[1].characters === 'Question number 1?')
check('question is 16 semibold', first[1].fontSize === '16' && first[1].fontWeight === '600')
check('details are 11 regular and faded', first[0].fontSize === '11' && first[0].fontWeight === '400' && first[0].opacity === 0.6)
check('texts fill the card width', first.every((t) => t.layoutChild && t.layoutChild.horizontalSizing === 'fill'))
check('texts grow in height', first.every((t) => t.growType === 'auto-height'))
check('a card with no meta has only the question', cards[3].children.length === 1 && cards[3].children[0].name === 'Question')
check('the block is selected', fake.penpot.selection.length === 1 && fake.penpot.selection[0] === block)
check('the view zooms to the block', fake.penpot.zoomed && fake.penpot.zoomed[0] === block)
check('no text is left loose on the page', fake.root.children.every((c) => c.type === 'board'))

fake.send({ type: 'insert', title: 'Visitor questions', items: items.slice(0, 2) })
const again = fake.root.children.filter((c) => c.type === 'board')
check('a second run adds a second block', again.length === 2)
check('the second block lands 200 under the first', again[1].y === block.y + block.height + 200, String(again[1].y))
check('the second block keeps the left edge', again[1].x === block.x)

fake.send({ type: 'nonsense' })
fake.send(null)
check('unknown messages are ignored', fake.toUi.filter((m) => m.type === 'error').length === 1)

fake.penpot.createText = () => null
fake.send({ type: 'insert', title: 'x', items: items.slice(0, 1) })
check('a failed text layer reports an error', fake.toUi.some((m) => m.type === 'error' && /could not create a text/.test(m.message)))

fake.send({ type: 'close' })
check('close ends the plugin', fake.penpot.closed === true)

// ---------------------------------------------------------------- manifest

console.log('\nmanifest')
const manifest = JSON.parse(fs.readFileSync(path.join(ROOT, 'public', 'manifest.json'), 'utf8'))
check('manifest version 2 for relative paths', manifest.version === 2)
check('manifest code file exists', fs.existsSync(path.join(ROOT, 'public', manifest.code)))
check('manifest icon exists', fs.existsSync(path.join(ROOT, 'public', manifest.icon)))
check('manifest asks only for what it uses', JSON.stringify(manifest.permissions.slice().sort()) === JSON.stringify(['allow:localstorage', 'content:write']))

console.log('\n' + passed + ' passed, ' + failed + ' failed')
process.exit(failed ? 1 : 0)

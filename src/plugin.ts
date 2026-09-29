// Customer Questions by Asyntai, for Penpot.
//
// The panel (public/index.html) talks to the Asyntai API. This file only draws
// on the canvas and keeps the API key in the plugin's own storage.

import type { Board, Shape, Text } from '@penpot/plugin-types'

const CARD_FILL = '#F2F2F2'
const TEXT_COLOR = '#000000'
const CARD_SIZE = 240
const COLUMNS = 5
const GAP = 40
const PADDING = 80
const HEADER = 140

const KEY_STORAGE = 'asyntai-api-key'

interface InsertItem {
    question: string
    meta: string
}

interface UiMessage {
    type: string
    apiKey?: string
    title?: string
    items?: InsertItem[]
    height?: number
}

penpot.ui.open('Customer Questions by Asyntai', `?theme=${penpot.theme}`, {
    width: 360,
    height: 540,
})

penpot.on('themechange', (theme) => {
    penpot.ui.sendMessage({ type: 'theme', theme: theme })
})

penpot.ui.onMessage<UiMessage>((msg) => {
    try {
        handle(msg)
    } catch (error) {
        const fault = error as { message?: string }
        const message = fault && fault.message ? fault.message : String(error)
        penpot.ui.sendMessage({ type: 'error', message: message })
    }
})

function handle(msg: UiMessage): void {
    if (!msg || typeof msg.type !== 'string') {
        return
    }

    if (msg.type === 'ready') {
        penpot.ui.sendMessage({
            type: 'init',
            apiKey: readKey(),
            theme: penpot.theme,
        })
        return
    }

    if (msg.type === 'save-key') {
        penpot.localStorage.setItem(KEY_STORAGE, msg.apiKey || '')
        return
    }

    if (msg.type === 'forget-key') {
        penpot.localStorage.removeItem(KEY_STORAGE)
        return
    }

    if (msg.type === 'resize' && typeof msg.height === 'number') {
        penpot.ui.resize(360, Math.max(240, Math.min(720, Math.round(msg.height))))
        return
    }

    if (msg.type === 'insert') {
        const items = msg.items || []
        if (items.length === 0) {
            penpot.ui.sendMessage({ type: 'error', message: 'There is nothing to add.' })
            return
        }
        const count = insert(msg.title || 'Visitor questions', items)
        penpot.ui.sendMessage({ type: 'inserted', count: count })
        return
    }

    if (msg.type === 'close') {
        penpot.closePlugin()
    }
}

function readKey(): string {
    const stored = penpot.localStorage.getItem(KEY_STORAGE)
    return typeof stored === 'string' ? stored : ''
}

function insert(title: string, items: InsertItem[]): number {
    const rows = Math.ceil(items.length / COLUMNS)
    const columns = Math.min(items.length, COLUMNS)
    const step = CARD_SIZE + GAP
    const width = PADDING * 2 + columns * step - GAP
    const height = PADDING * 2 + HEADER + rows * step - GAP

    // The block goes under everything already on the page, so a second run
    // never covers the first one.
    const spot = freeSpot()

    const container = penpot.createBoard()
    container.name = title
    container.x = spot.x
    container.y = spot.y
    container.resize(width, height)
    container.fills = [{ fillColor: '#FFFFFF', fillOpacity: 1 }]
    container.clipContent = false

    const heading = makeText(title, '32', '600')
    heading.name = 'Title'
    heading.growType = 'auto-width'
    place(container, heading, PADDING, PADDING)

    for (let i = 0; i < items.length; i++) {
        const card = buildCard(items[i])
        place(
            container,
            card,
            PADDING + (i % COLUMNS) * step,
            PADDING + HEADER + Math.floor(i / COLUMNS) * step,
        )
    }

    penpot.selection = [container]
    penpot.viewport.zoomIntoView([container])
    return items.length
}

// One question on a grey card, with the count and the page underneath.
function buildCard(item: InsertItem): Board {
    const card = penpot.createBoard()
    card.name = item.question.slice(0, 60)
    card.resize(CARD_SIZE, CARD_SIZE)
    card.borderRadius = 8
    card.fills = [{ fillColor: CARD_FILL, fillOpacity: 1 }]
    card.clipContent = true

    const layout = card.addFlexLayout()
    layout.dir = 'column'
    layout.rowGap = 12
    layout.topPadding = 20
    layout.rightPadding = 20
    layout.bottomPadding = 20
    layout.leftPadding = 20
    layout.alignItems = 'stretch'

    // Penpot lays out a flex column from the top of the layer stack down, and
    // every append goes on top. So the line that must show last goes in first.
    if (item.meta) {
        const meta = makeText(item.meta, '11', '400')
        meta.name = 'Details'
        meta.growType = 'auto-height'
        meta.opacity = 0.6
        layout.appendChild(meta)
        fillWidth(meta)
    }

    const question = makeText(item.question, '16', '600')
    question.name = 'Question'
    question.growType = 'auto-height'
    layout.appendChild(question)
    fillWidth(question)

    return card
}

function makeText(characters: string, size: string, weight: string): Text {
    const text = penpot.createText(characters)
    if (!text) {
        throw new Error('Penpot could not create a text layer.')
    }
    text.fontSize = size
    text.fontWeight = weight
    text.fills = [{ fillColor: TEXT_COLOR, fillOpacity: 1 }]
    return text
}

// A text in a flex column takes the card width. layoutChild only exists once
// the text sits inside the layout, so this runs after appendChild.
function fillWidth(text: Text): void {
    if (text.layoutChild) {
        text.layoutChild.horizontalSizing = 'fill'
    }
}

// x and y are canvas positions, so a child is placed relative to its parent
// after it is appended.
function place(parent: Board, child: Shape, offsetX: number, offsetY: number): void {
    parent.appendChild(child)
    child.x = parent.x + offsetX
    child.y = parent.y + offsetY
}

// The next empty band under everything already on the page.
function freeSpot(): { x: number; y: number } {
    const page = penpot.currentPage
    if (!page) {
        return { x: 0, y: 0 }
    }
    let bottom: number | null = null
    let left: number | null = null
    for (const shape of page.findShapes()) {
        if (!shape.parent || shape.parent.id !== page.root.id) {
            continue
        }
        bottom = bottom === null ? shape.y + shape.height : Math.max(bottom, shape.y + shape.height)
        left = left === null ? shape.x : Math.min(left, shape.x)
    }
    if (bottom === null || left === null) {
        return { x: 0, y: 0 }
    }
    return { x: left, y: bottom + 200 }
}

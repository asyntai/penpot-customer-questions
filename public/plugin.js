"use strict";
(() => {
  var __getOwnPropNames = Object.getOwnPropertyNames;
  var __commonJS = (cb, mod) => function __require() {
    try {
      return mod || (0, cb[__getOwnPropNames(cb)[0]])((mod = { exports: {} }).exports, mod), mod.exports;
    } catch (e) {
      throw mod = 0, e;
    }
  };

  // src/plugin.ts
  var require_plugin = __commonJS({
    "src/plugin.ts"() {
      var CARD_FILL = "#F2F2F2";
      var TEXT_COLOR = "#000000";
      var CARD_SIZE = 240;
      var COLUMNS = 5;
      var GAP = 40;
      var PADDING = 80;
      var HEADER = 140;
      var KEY_STORAGE = "asyntai-api-key";
      penpot.ui.open("Customer Questions by Asyntai", `?theme=${penpot.theme}`, {
        width: 360,
        height: 540
      });
      penpot.on("themechange", (theme) => {
        penpot.ui.sendMessage({ type: "theme", theme });
      });
      penpot.ui.onMessage((msg) => {
        try {
          handle(msg);
        } catch (error) {
          const fault = error;
          const message = fault && fault.message ? fault.message : String(error);
          penpot.ui.sendMessage({ type: "error", message });
        }
      });
      function handle(msg) {
        if (!msg || typeof msg.type !== "string") {
          return;
        }
        if (msg.type === "ready") {
          penpot.ui.sendMessage({
            type: "init",
            apiKey: readKey(),
            theme: penpot.theme
          });
          return;
        }
        if (msg.type === "save-key") {
          penpot.localStorage.setItem(KEY_STORAGE, msg.apiKey || "");
          return;
        }
        if (msg.type === "forget-key") {
          penpot.localStorage.removeItem(KEY_STORAGE);
          return;
        }
        if (msg.type === "resize" && typeof msg.height === "number") {
          penpot.ui.resize(360, Math.max(240, Math.min(720, Math.round(msg.height))));
          return;
        }
        if (msg.type === "insert") {
          const items = msg.items || [];
          if (items.length === 0) {
            penpot.ui.sendMessage({ type: "error", message: "There is nothing to add." });
            return;
          }
          const count = insert(msg.title || "Visitor questions", items);
          penpot.ui.sendMessage({ type: "inserted", count });
          return;
        }
        if (msg.type === "close") {
          penpot.closePlugin();
        }
      }
      function readKey() {
        const stored = penpot.localStorage.getItem(KEY_STORAGE);
        return typeof stored === "string" ? stored : "";
      }
      function insert(title, items) {
        const rows = Math.ceil(items.length / COLUMNS);
        const columns = Math.min(items.length, COLUMNS);
        const step = CARD_SIZE + GAP;
        const width = PADDING * 2 + columns * step - GAP;
        const height = PADDING * 2 + HEADER + rows * step - GAP;
        const spot = freeSpot();
        const container = penpot.createBoard();
        container.name = title;
        container.x = spot.x;
        container.y = spot.y;
        container.resize(width, height);
        container.fills = [{ fillColor: "#FFFFFF", fillOpacity: 1 }];
        container.clipContent = false;
        const heading = makeText(title, "32", "600");
        heading.name = "Title";
        heading.growType = "auto-width";
        place(container, heading, PADDING, PADDING);
        for (let i = 0; i < items.length; i++) {
          const card = buildCard(items[i]);
          place(
            container,
            card,
            PADDING + i % COLUMNS * step,
            PADDING + HEADER + Math.floor(i / COLUMNS) * step
          );
        }
        penpot.selection = [container];
        penpot.viewport.zoomIntoView([container]);
        return items.length;
      }
      function buildCard(item) {
        const card = penpot.createBoard();
        card.name = item.question.slice(0, 60);
        card.resize(CARD_SIZE, CARD_SIZE);
        card.borderRadius = 8;
        card.fills = [{ fillColor: CARD_FILL, fillOpacity: 1 }];
        card.clipContent = true;
        const layout = card.addFlexLayout();
        layout.dir = "column";
        layout.rowGap = 12;
        layout.topPadding = 20;
        layout.rightPadding = 20;
        layout.bottomPadding = 20;
        layout.leftPadding = 20;
        layout.alignItems = "stretch";
        if (item.meta) {
          const meta = makeText(item.meta, "11", "400");
          meta.name = "Details";
          meta.growType = "auto-height";
          meta.opacity = 0.6;
          layout.appendChild(meta);
          fillWidth(meta);
        }
        const question = makeText(item.question, "16", "600");
        question.name = "Question";
        question.growType = "auto-height";
        layout.appendChild(question);
        fillWidth(question);
        return card;
      }
      function makeText(characters, size, weight) {
        const text = penpot.createText(characters);
        if (!text) {
          throw new Error("Penpot could not create a text layer.");
        }
        text.fontSize = size;
        text.fontWeight = weight;
        text.fills = [{ fillColor: TEXT_COLOR, fillOpacity: 1 }];
        return text;
      }
      function fillWidth(text) {
        if (text.layoutChild) {
          text.layoutChild.horizontalSizing = "fill";
        }
      }
      function place(parent, child, offsetX, offsetY) {
        parent.appendChild(child);
        child.x = parent.x + offsetX;
        child.y = parent.y + offsetY;
      }
      function freeSpot() {
        const page = penpot.currentPage;
        if (!page) {
          return { x: 0, y: 0 };
        }
        let bottom = null;
        let left = null;
        for (const shape of page.findShapes()) {
          if (!shape.parent || shape.parent.id !== page.root.id) {
            continue;
          }
          bottom = bottom === null ? shape.y + shape.height : Math.max(bottom, shape.y + shape.height);
          left = left === null ? shape.x : Math.min(left, shape.x);
        }
        if (bottom === null || left === null) {
          return { x: 0, y: 0 };
        }
        return { x: left, y: bottom + 200 };
      }
    }
  });
  require_plugin();
})();

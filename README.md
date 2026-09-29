# Customer Questions by Asyntai, for Penpot

Put the real questions your website visitors ask on the Penpot canvas.

[Asyntai](https://asyntai.com) is an AI chatbot that answers visitors on your
website. This plugin reads those chats and places the questions in your Penpot
file as cards. The same question from many visitors becomes one card with its
count, and the most asked question comes first. Under each question you see the
page the visitor was on, the country and the topic.

Teams use it to plan a help centre, to design a FAQ page with real questions,
or to start a workshop with what customers really ask.

## What you need

- Penpot, on penpot.app or on your own Penpot server
- An Asyntai account on the Starter plan or higher, for the API key

## Install

1. In Asyntai, open **Settings**, then **API**, and copy your API key.
2. Open a file in Penpot and press **Ctrl + Alt + P**.
3. Paste this address and press **Install**:

   ```
   https://asyntai.github.io/penpot-customer-questions/manifest.json
   ```

4. Press **Allow**, then **Open**.
5. Paste your API key and press **Connect**. Penpot keeps it, so you type it one time.

## Use

Choose a website, a period (the last 7, 30 or 90 days, or all time) and how many
questions you want. Press **Add to canvas**.

The cards land on one board under everything already on the page, five to a
row. Each card is a normal Penpot board with a flex layout, with text layers
named **Question** and **Details**, so you can restyle it or move it into your
own design. Run the plugin again for a new set; it never covers the old one.

To connect another Asyntai account, press **Use another API key**.

Full guide: https://asyntai.com/documentation/integrations/penpot/

## Develop

```bash
npm install
npm run typecheck
npm run build
npm test
```

`npm run build` bundles `src/plugin.ts` into `public/plugin.js`. The folder
`public/` is the whole plugin as Penpot loads it.

To run it in a Penpot of your own:

```bash
python test/serve.py --mock
```

Then install `http://localhost:4400/manifest.json` in Penpot and connect with
the key `demo-key`. `--mock` answers the Asyntai API from
`test/demo-sessions.json`, a made-up outdoor shop.

## Support

hello@asyntai.com

## License

MIT

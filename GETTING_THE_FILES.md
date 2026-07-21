# Getting the OfficeSpeak files onto your computer

`README.md` asks you to open a couple of files that live inside
"OfficeSpeak" — this page is how to actually get them onto your computer if
you don't already have them. If someone already handed you an "OfficeSpeak"
folder directly (by email, a shared drive, or a USB stick), you can skip this
and go straight back to `README.md`.

**You can read this page and click its links before you've downloaded
anything** — that's the whole point of it. If you were sent straight to this
page, keep going; you don't need `README.md` yet, it's what you'll
open (your own local copy of it) once you finish Step 3 below.

*(For whoever is inviting a new tester: the two links to hand someone with
nothing downloaded yet are
[README.md on GitHub](https://github.com/kmchandy/OfficeSpeak/blob/main/README.md)
and
[GETTING_THE_FILES.md on GitHub](https://github.com/kmchandy/OfficeSpeak/blob/main/GETTING_THE_FILES.md)
— either works as a starting point; GitHub renders the file and its links
work immediately, with nothing to install first.)*

## What GitHub is

GitHub is a website where people store and share folders of files for
software projects — a "repository" (or "repo" for short) is just one such
folder, kept on that website. OfficeSpeak's repo is public, meaning anyone
with the web address can look at it or download a copy, no account needed.

## Step 1 — Download the whole folder as a ZIP

1. Open a web browser and go to:
   **https://github.com/kmchandy/OfficeSpeak**
2. Look for a green button labeled **`< > Code`**, near the top of the page,
   and click it.
3. A small menu drops down. Click **Download ZIP** (near the bottom of that
   menu).
4. Your browser downloads a file — usually into a folder called **Downloads**
   — named something like `OfficeSpeak-main.zip`.

## Step 2 — Unzip it

A ZIP file is a folder that's been compressed into a single file to make it
smaller to download; "unzipping" turns it back into a normal folder you can
open and browse.

- **On a Mac:** find `OfficeSpeak-main.zip` in Finder (usually in
  Downloads) and just **double-click it**. A new folder,
  `OfficeSpeak-main`, appears right next to it — that's your OfficeSpeak
  folder.
- **On Windows:** right-click `OfficeSpeak-main.zip` and choose
  **Extract All...**, then click **Extract**. You'll get the same
  `OfficeSpeak-main` folder.

Rename that folder to `OfficeSpeak` if you like (not required — `README.md`
just means "wherever you put this folder" whenever it says `OfficeSpeak/...`).

## Step 3 — Find the two things Stage 1 needs

Open the folder you just unzipped, then open `offices`, then
`claude_project`. Inside, you'll find:

- **`start_instructions.md`** — a text file. Double-click it to open it
  (in TextEdit, Notepad, or your browser — any of those is fine), then
  select all the text and copy it. This is what gets pasted into the
  claude.ai Project's custom instructions in `README.md`'s Stage 1, step 1.
- **`start_gallery`** — a folder containing several `.md` files. `README.md`
  asks you to upload *every file inside this folder* (not the folder itself)
  as Project knowledge.

That's everything Stage 1 needs. You will not need to open, read, or
understand anything else in the folder for Stage 1.

## If you'll also be doing Stage 2

Stage 2 (running the office someone built) needs this same downloaded
`OfficeSpeak` folder, plus its companion repo, **DisSysLab**, downloaded the
same way from **https://github.com/kmchandy/DisSysLab** (green `Code` button
→ Download ZIP → unzip, exactly as above). `README.md`'s Stage 2 section
picks up from there. Right now, you don't have to do Stage 2 yourself at all
— see `README.md`'s note about sending your Stage 1 hand-off file to your
OfficeSpeak contact instead.

## Getting updates later

If your contact tells you the files changed and you need the newest version,
just repeat Step 1 and Step 2 above — download a fresh ZIP and unzip it again.
It won't touch or merge with your old copy; you'll end up with two folders,
so it's fine to delete the old one once you've confirmed the new one has what
you need.

## An alternative to the ZIP: "cloning" (better if you'll want updates often)

The ZIP method above gives you a snapshot — a copy frozen at the moment you
downloaded it. **Cloning** instead gives you a *live* copy that you can update
later with a single click or command, without re-downloading and re-unzipping
by hand every time. It's a little more setup up front, so the ZIP method
above is still the faster choice for a one-time try; reach for cloning if you
know you'll be coming back to this folder repeatedly.

- **If you don't want to use a terminal at all:** install the free
  **[GitHub Desktop](https://desktop.github.com)** app, then follow GitHub's
  own short guide — [Cloning and forking repositories from GitHub
  Desktop](https://docs.github.com/en/desktop/adding-and-cloning-repositories/cloning-and-forking-repositories-from-github-desktop).
  It's a normal-looking app: paste in `https://github.com/kmchandy/OfficeSpeak`,
  click Clone, done. Updating later is one button ("Fetch origin" / "Pull").
- **If you're comfortable in a terminal** (this is the route Stage 2 will
  likely use): GitHub's own step-by-step guide —
  [Cloning a repository](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository)
  — covers it in full, including what to do if something goes wrong. The
  short version:
  ```bash
  git clone https://github.com/kmchandy/OfficeSpeak.git
  git clone https://github.com/kmchandy/DisSysLab.git
  ```
  and, later, `git pull` inside either folder to get updates.

Either way, once you have the folder, Step 3 above (finding
`start_instructions.md` and `start_gallery`) is exactly the same.

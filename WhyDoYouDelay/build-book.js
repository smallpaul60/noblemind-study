// Build Why Do You Delay? docx from the markdown source.
// Parses the canonical markdown at /home/claude/why-do-you-delay-book.md
// and produces a formatted Word document.

const fs = require('fs');
const {
  Document, Packer, Paragraph, TextRun, Header, Footer,
  AlignmentType, PageOrientation, LevelFormat,
  TabStopType, TabStopPosition,
  PageNumber, PageBreak, HeadingLevel, BorderStyle
} = require('docx');

const SRC = '/home/claude/why-do-you-delay-book.md';
const OUT = '/home/claude/why-do-you-delay-book.docx';

const BOOK_TITLE = 'Why Do You Delay?';
const BOOK_SUBTITLE = 'Baptism, Salvation, and What the Bible Actually Says';

// ---------- inline formatting: **bold** / *italic* ----------
function parseInline(text) {
  // Supports **bold** and *italic* (non-overlapping, non-greedy).
  // Returns an array of TextRun objects.
  const runs = [];
  const re = /(\*\*([^*]+)\*\*|\*([^*]+)\*)/g;
  let last = 0;
  let m;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) {
      runs.push(new TextRun({ text: text.slice(last, m.index) }));
    }
    if (m[2] !== undefined) {
      runs.push(new TextRun({ text: m[2], bold: true }));
    } else if (m[3] !== undefined) {
      runs.push(new TextRun({ text: m[3], italics: true }));
    }
    last = re.lastIndex;
  }
  if (last < text.length) {
    runs.push(new TextRun({ text: text.slice(last) }));
  }
  return runs;
}

function parseInlineItalic(text) {
  // Block quotes: the whole paragraph renders italic. The markdown convention
  // here is that quote text is wrapped in *...* to signal italic. If the
  // content is wrapped in a single *...* pair (not **...**), strip them.
  // Then handle any **bold** markers inside.
  let content = text.trim();
  if (content.length > 2 &&
      content[0] === '*' && content[1] !== '*' &&
      content[content.length - 1] === '*' && content[content.length - 2] !== '*') {
    content = content.slice(1, -1);
  }

  const runs = [];
  const re = /\*\*([^*]+)\*\*/g;
  let last = 0;
  let m;
  while ((m = re.exec(content)) !== null) {
    if (m.index > last) {
      runs.push(new TextRun({ text: content.slice(last, m.index), italics: true }));
    }
    runs.push(new TextRun({ text: m[1], italics: true, bold: true }));
    last = re.lastIndex;
  }
  if (last < content.length) {
    runs.push(new TextRun({ text: content.slice(last), italics: true }));
  }
  return runs;
}

// ---------- paragraph helpers ----------
function bodyParagraph(text) {
  return new Paragraph({
    spacing: { before: 0, after: 160, line: 320 },
    alignment: AlignmentType.JUSTIFIED,
    children: parseInline(text)
  });
}

// Left border (vertical bar) shared by every paragraph in a block quote.
// size is in 1/8 points; 16 = 2pt thick. space is the gap between the bar
// and the text, in points.
const QUOTE_BAR = {
  left: { style: BorderStyle.SINGLE, size: 16, color: '888888', space: 12 }
};

function blockQuoteItalic(text) {
  return new Paragraph({
    spacing: { before: 120, after: 0, line: 320 },
    indent: { left: 720, right: 720 },
    border: QUOTE_BAR,
    children: parseInlineItalic(text)
  });
}

function citationLine(text) {
  return new Paragraph({
    spacing: { before: 0, after: 200, line: 320 },
    indent: { left: 720, right: 720 },
    alignment: AlignmentType.RIGHT,
    border: QUOTE_BAR,
    children: [new TextRun({ text: text })]
  });
}

function chapterHeading(num, title) {
  return [
    new Paragraph({ children: [new PageBreak()] }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 720, after: 240 },
      children: [new TextRun({ text: `Chapter ${num}`, size: 24, italics: true, color: '666666' })]
    }),
    new Paragraph({
      heading: HeadingLevel.HEADING_1,
      alignment: AlignmentType.CENTER,
      spacing: { before: 0, after: 480 },
      children: [new TextRun({ text: title, size: 40, bold: true })]
    })
  ];
}

function partHeading(label, title, intro) {
  const out = [
    new Paragraph({ children: [new PageBreak()] }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 1440, after: 240 },
      children: [new TextRun({ text: label.toUpperCase(), size: 28, italics: true, color: '666666', characterSpacing: 40 })]
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 0, after: 720 },
      children: [new TextRun({ text: title, size: 44, bold: true })]
    })
  ];
  if (intro) {
    out.push(new Paragraph({
      spacing: { before: 480, after: 240, line: 320 },
      alignment: AlignmentType.JUSTIFIED,
      indent: { left: 360, right: 360 },
      children: parseInline(intro)
    }));
  }
  return out;
}

function subheading(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 360, after: 160 },
    children: [new TextRun({ text: text, size: 28, bold: true })]
  });
}

function epilogueHeading(title) {
  return [
    new Paragraph({ children: [new PageBreak()] }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 1440, after: 240 },
      children: [new TextRun({ text: 'EPILOGUE', size: 28, italics: true, color: '666666', characterSpacing: 40 })]
    }),
    new Paragraph({
      heading: HeadingLevel.HEADING_1,
      alignment: AlignmentType.CENTER,
      spacing: { before: 0, after: 480 },
      children: [new TextRun({ text: title, size: 40, bold: true })]
    })
  ];
}

function prefaceHeading(title) {
  return [
    new Paragraph({ children: [new PageBreak()] }),
    new Paragraph({
      heading: HeadingLevel.HEADING_1,
      alignment: AlignmentType.CENTER,
      spacing: { before: 1440, after: 480 },
      children: [new TextRun({ text: title, size: 40, bold: true })]
    })
  ];
}

// ---------- title page & TOC ----------
function titlePage() {
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 2880, after: 480 },
      children: [new TextRun({ text: BOOK_TITLE, size: 64, bold: true })]
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 0, after: 2880 },
      children: [new TextRun({ text: BOOK_SUBTITLE, size: 28, italics: true, color: '555555' })]
    })
  ];
}

// Copyright page — sits on the verso after the title page.
// Small, centered text with generous spacing between blocks.
function copyrightPage() {
  const SMALL = 20;       // 10pt
  const SMALL_LINE = 260; // compact line spacing
  const block = (text, opts = {}) => new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: opts.before ?? 0, after: opts.after ?? 240, line: SMALL_LINE },
    children: [new TextRun({ text: text, size: SMALL, italics: !!opts.italics })]
  });
  const blockRuns = (runs, opts = {}) => new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: opts.before ?? 0, after: opts.after ?? 240, line: SMALL_LINE },
    children: runs
  });

  return [
    new Paragraph({ children: [new PageBreak()] }),
    // Title block at top
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 720, after: 120, line: SMALL_LINE },
      children: [new TextRun({ text: BOOK_TITLE, size: 28, bold: true })]
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 0, after: 480, line: SMALL_LINE },
      children: [new TextRun({ text: BOOK_SUBTITLE, size: SMALL, italics: true, color: '555555' })]
    }),
    // Copyright line
    block('Copyright \u00A9 2026 by Paul Hainline', { after: 320 }),
    // All rights reserved paragraph
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 0, after: 320, line: SMALL_LINE },
      indent: { left: 720, right: 720 },
      children: [new TextRun({
        text: 'All rights reserved. No portion of this book may be reproduced, stored in a retrieval system, or transmitted in any form or by any means \u2014 electronic, mechanical, photocopy, recording, or any other \u2014 except for brief quotations in printed reviews, without the prior written permission of the publisher.',
        size: SMALL
      })]
    }),
    // Edition
    block('First Edition, 2026', { after: 320 }),
    // Publisher
    block('Published by NobleMind Press', { after: 40 }),
    block('noblemind.study', { after: 320, italics: true }),
    // NASB permissions notice (uses the Lockman-required wording verbatim)
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 0, after: 320, line: SMALL_LINE },
      indent: { left: 720, right: 720 },
      children: [new TextRun({
        text: 'Scripture quotations taken from the (NASB\u00AE) New American Standard Bible\u00AE, Copyright \u00A9 1960, 1971, 1977, 1995 by The Lockman Foundation. Used by permission. All rights reserved. www.Lockman.org',
        size: SMALL
      })]
    }),
    // Print origin
    block('Printed in the United States of America')
  ];
}

// Dedication page — italic text, centered horizontally, pushed toward
// vertical center of the page using a stack of empty paragraphs (Word
// collapses spacing.before at the top of a new page).
function dedicationPage() {
  const out = [new Paragraph({ children: [new PageBreak()] })];
  // Push down ~12 empty lines to land near vertical center.
  for (let i = 0; i < 12; i++) {
    out.push(new Paragraph({ children: [new TextRun({ text: '' })] }));
  }
  out.push(new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 0, after: 0, line: 360 },
    children: [new TextRun({
      text: 'For those who seek truth with an open mind and an honest heart \u2014',
      size: 26, italics: true
    })]
  }));
  out.push(new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 0, after: 0, line: 360 },
    children: [new TextRun({
      text: 'who, like the Bereans, examine the Scriptures',
      size: 26, italics: true
    })]
  }));
  out.push(new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 0, after: 0, line: 360 },
    children: [new TextRun({
      text: 'to see whether these things are so.',
      size: 26, italics: true
    })]
  }));
  return out;
}

function tocTopEntry(text) {
  return new Paragraph({
    spacing: { before: 240, after: 120 },
    children: [new TextRun({ text: text, size: 26, bold: true })]
  });
}

function tocPartHeader(text) {
  return new Paragraph({
    spacing: { before: 480, after: 160 },
    children: [new TextRun({ text: text, size: 26, bold: true, italics: true, color: '333333' })]
  });
}

function tocChapterEntry(text) {
  return new Paragraph({
    spacing: { before: 40, after: 40 },
    indent: { left: 360 },
    children: [new TextRun({ text: text, size: 24 })]
  });
}

function contentsPage() {
  return [
    new Paragraph({ children: [new PageBreak()] }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 720, after: 480 },
      children: [new TextRun({ text: 'Contents', size: 40, bold: true })]
    }),
    tocTopEntry('Preface'),

    tocPartHeader('Part One — What the Lord and His Apostles Taught'),
    tocChapterEntry('Chapter 1 — The Command'),
    tocChapterEntry('Chapter 2 — Born of Water and the Spirit'),
    tocChapterEntry('Chapter 3 — What Baptism Is'),
    tocChapterEntry('Chapter 4 — The Baptisms of Scripture, and the One That Remains'),
    tocChapterEntry('Chapter 5 — What the Apostles Taught'),

    tocPartHeader('Part Two — What the Early Church Did'),
    tocChapterEntry('Chapter 6 — Every Conversion in Acts'),
    tocChapterEntry('Chapter 7 — Where Is the Sinner\u2019s Prayer?'),
    tocChapterEntry('Chapter 8 — \u201CWhat Must I Do?\u201D'),

    tocPartHeader('Part Three — Answering the Common Objections'),
    tocChapterEntry('Chapter 9 — Not an Outward Expression of an Inward Grace'),
    tocChapterEntry('Chapter 10 — \u201CBut We Are Saved by Grace, Not Works\u201D'),
    tocChapterEntry('Chapter 11 — Not by Faith Alone'),
    tocChapterEntry('Chapter 12 — What About the Thief on the Cross?'),
    tocChapterEntry('Chapter 13 — Calling on the Name of the Lord'),

    tocTopEntry('Epilogue — Why Do You Delay?')
  ];
}

// ---------- markdown parser ----------
// Parses the book's structured markdown into a sequence of docx paragraphs.
// It understands:
//   # Part heading (followed by an intro paragraph until the next ---)
//   ## Chapter N — Title           (chapter)
//   ## Preface                      (preface)
//   # Epilogue — Title             (epilogue)
//   ### Subheading                  (chapter subheading)
//   > *quote text*                  (block quote line)
//   > — Citation                    (citation line)
//   ---                             (horizontal rule / section break; ignored)
//   blank line                      (paragraph separator)
//   otherwise                       (body paragraph)
function buildDocumentChildren() {
  const md = fs.readFileSync(SRC, 'utf8');
  const lines = md.split('\n');

  const children = [];
  children.push(...titlePage());
  children.push(...copyrightPage());
  children.push(...dedicationPage());
  children.push(...contentsPage());

  // Find the Preface and skip everything before it (title block, Contents list in md)
  let i = 0;
  while (i < lines.length && !/^##\s+Preface\s*$/.test(lines[i])) i++;
  if (i >= lines.length) throw new Error('Preface not found');

  // Paragraph accumulator — body paragraphs span multiple lines in markdown
  let para = [];
  function flushPara() {
    if (para.length === 0) return;
    const joined = para.join(' ').trim();
    if (joined) children.push(bodyParagraph(joined));
    para = [];
  }

  // Quote block accumulator — a block quote may span multiple lines
  // The first line(s) are the quoted text (> *...*), final line is the citation (> — ...)
  let quoteText = [];
  function flushQuote() {
    if (quoteText.length === 0) return;
    // Last line is citation if it starts with em-dash
    const lastLine = quoteText[quoteText.length - 1];
    let citation = null;
    let bodyLines = quoteText;
    if (/^—\s/.test(lastLine)) {
      citation = lastLine;
      bodyLines = quoteText.slice(0, -1);
    }
    const bodyText = bodyLines.join(' ').trim();
    if (bodyText) children.push(blockQuoteItalic(bodyText));
    if (citation) children.push(citationLine(citation));
    quoteText = [];
  }

  for (; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();

    // Horizontal rules separate sections but have no visual in docx
    if (trimmed === '---') {
      flushPara();
      flushQuote();
      continue;
    }

    // Blank line — end any open paragraph/quote
    if (trimmed === '') {
      flushPara();
      flushQuote();
      continue;
    }

    // Block quote line
    if (trimmed.startsWith('>')) {
      flushPara();
      // Strip the leading '> ' and collect
      const content = trimmed.replace(/^>\s?/, '');
      quoteText.push(content);
      continue;
    }

    // Flush any pending quote before a new non-quote line
    if (quoteText.length > 0) flushQuote();

    // Epilogue (starts with single # Epilogue)
    let m;
    if ((m = trimmed.match(/^#\s+Epilogue\s+—\s+(.+)$/))) {
      flushPara();
      children.push(...epilogueHeading(m[1].trim()));
      continue;
    }

    // Part heading: # Part Something — Rest
    if ((m = trimmed.match(/^#\s+(Part\s+\S+)\s+—\s+(.+)$/))) {
      flushPara();
      // Collect the intro paragraph that follows (until next --- or ##)
      const label = m[1];
      const title = m[2].trim();
      let intro = [];
      let j = i + 1;
      // Skip blank lines
      while (j < lines.length && lines[j].trim() === '') j++;
      // Collect intro paragraph(s) until we hit --- or a heading
      while (j < lines.length) {
        const t = lines[j].trim();
        if (t === '---' || /^#/.test(t)) break;
        if (t === '') {
          // allow single blank within intro, then stop
          j++;
          if (j < lines.length && lines[j].trim() !== '' && !/^#/.test(lines[j].trim()) && lines[j].trim() !== '---') {
            // keep going
          } else {
            break;
          }
          continue;
        }
        intro.push(t);
        j++;
      }
      children.push(...partHeading(label, title, intro.join(' ').trim() || null));
      i = j - 1;
      continue;
    }

    // Preface heading
    if (/^##\s+Preface\s*$/.test(trimmed)) {
      flushPara();
      children.push(...prefaceHeading('Preface'));
      continue;
    }

    // Chapter heading: ## Chapter N — Title
    if ((m = trimmed.match(/^##\s+Chapter\s+(\d+)\s+—\s+(.+)$/))) {
      flushPara();
      children.push(...chapterHeading(m[1], m[2].trim()));
      continue;
    }

    // Subheading: ###
    if ((m = trimmed.match(/^###\s+(.+)$/))) {
      flushPara();
      children.push(subheading(m[1].trim()));
      continue;
    }

    // Skip any other top-level heading (the title block at the top)
    if (/^#/.test(trimmed)) {
      flushPara();
      continue;
    }

    // Otherwise: body text — accumulate into the current paragraph.
    // Consecutive non-blank body lines belong to the same paragraph.
    para.push(trimmed);
  }

  flushPara();
  flushQuote();

  return children;
}

// ---------- build & write ----------
const children = buildDocumentChildren();

const doc = new Document({
  styles: {
    default: { document: { run: { font: 'Georgia', size: 24 } } },
    paragraphStyles: [
      {
        id: 'Heading1',
        name: 'Heading 1',
        basedOn: 'Normal',
        next: 'Normal',
        quickFormat: true,
        run: { size: 40, bold: true, font: 'Georgia' },
        paragraph: { spacing: { before: 240, after: 240 }, outlineLevel: 0 }
      },
      {
        id: 'Heading2',
        name: 'Heading 2',
        basedOn: 'Normal',
        next: 'Normal',
        quickFormat: true,
        run: { size: 28, bold: true, font: 'Georgia' },
        paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 1 }
      }
    ]
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 }, // US Letter
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
      }
    },
    headers: {
      default: new Header({
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: BOOK_TITLE, italics: true, color: '888888', size: 20 })]
        })]
      })
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ children: [PageNumber.CURRENT], size: 20, color: '666666' })]
        })]
      })
    },
    children: children
  }]
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync(OUT, buf);
  console.log(`Wrote ${OUT} (${buf.length} bytes, ${children.length} paragraphs)`);
});

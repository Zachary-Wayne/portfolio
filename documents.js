const DOC_LIBRARIES = [
    'https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.9/katex.min.css',
    'https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.9/katex.min.js',
    'https://cdn.jsdelivr.net/npm/marked@12.0.2/marked.min.js'
];

const TOC_DEPTH = 3;

const loadedResources = new Map();
let docLibrariesReady = null;
let docCount = 0;

function loadResource(url) {
    if (!loadedResources.has(url)) {
        loadedResources.set(url, new Promise((resolve, reject) => {
            const el = url.endsWith('.css')
                ? Object.assign(document.createElement('link'), { rel: 'stylesheet', href: url })
                : Object.assign(document.createElement('script'), { src: url });
            el.onload = resolve;
            el.onerror = () => reject(new Error(`Failed to load ${url}`));
            document.head.appendChild(el);
        }));
    }
    return loadedResources.get(url);
}

function loadDocLibraries() {
    docLibrariesReady ??= Promise.all(DOC_LIBRARIES.map(loadResource)).then(configureMarked);
    return docLibrariesReady;
}

function renderMath(tex, displayMode) {
    return katex.renderToString(tex.replace(/⁡/g, ''), { displayMode, throwOnError: false, strict: false });
}

function configureMarked() {
    marked.use({
        extensions: [
            {
                name: 'blockMath',
                level: 'block',
                start: src => src.match(/^\$\$/m)?.index,
                tokenizer(src) {
                    const match = /^\$\$([\s\S]+?)\$\$[^\S\n]*(?:\n|$)/.exec(src);
                    if (match) return { type: 'blockMath', raw: match[0], text: match[1].trim() };
                },
                renderer: token => `<div class="math-block">${renderMath(token.text, true)}</div>`
            },
            {
                name: 'inlineMath',
                level: 'inline',
                start: src => src.indexOf('$'),
                tokenizer(src) {
                    const match = /^\$\$([\s\S]+?)\$\$/.exec(src) || /^\$([^\s$](?:[^$\n]*?[^\s$])?)\$/.exec(src);
                    if (match) {
                        return { type: 'inlineMath', raw: match[0], text: match[1].trim(), display: match[0].startsWith('$$') };
                    }
                },
                renderer: token => renderMath(token.text, token.display)
            },
            {
                name: 'wikilink',
                level: 'inline',
                start: src => src.indexOf('[['),
                tokenizer(src) {
                    const match = /^\[\[([^\]|#]+)(?:#([^\]|]+))?(?:\|([^\]]+))?\]\]/.exec(src);
                    if (match) {
                        const label = match[3] || (match[2] ? `${match[1]} › ${match[2]}` : match[1]);
                        return { type: 'wikilink', raw: match[0], text: label.trim() };
                    }
                },
                renderer: token => `<span class="wikilink">${marked.parseInline(token.text)}</span>`
            }
        ],
        renderer: {
            code(code, lang) {
                return lang === 'table-of-contents' ? '<nav class="doc-toc"></nav>' : false;
            }
        }
    });
}

function isRelativeUrl(url) {
    return url && !/^([a-z]+:|#|\/)/i.test(url);
}

function markdownToHtml(text, basePath) {
    const baseUrl = new URL(basePath, location.href);
    return marked.parse(text, {
        walkTokens(token) {
            if ((token.type === 'link' || token.type === 'image') && isRelativeUrl(token.href)) {
                token.href = new URL(token.href, baseUrl).href;
            }
        }
    });
}

function scrollToElement(target) {
    const scroller = target?.closest('.modal-scroll');
    if (!scroller) return;
    const offset = target.getBoundingClientRect().top - scroller.getBoundingClientRect().top;
    const tabBarHeight = (scroller.querySelector('.pane-tabs')?.offsetHeight || 0)
        + (scroller.querySelector('.modal-toc:not([hidden])')?.offsetHeight || 0);
    scroller.scrollTo({ top: scroller.scrollTop + offset - tabBarHeight - 8, behavior: 'smooth' });
}

function renderCallouts(container) {
    container.querySelectorAll('blockquote').forEach(quote => {
        const first = quote.querySelector('p');
        const match = first?.innerHTML.match(/^\[!(\w+)\]([^\n<]*)(?:\n|<br>)?/);
        if (!match) return;
        const type = match[1].toLowerCase();
        const title = match[2].trim().replace(/#(\w+)\s*/g, '$1 · ') || match[1];
        first.innerHTML = first.innerHTML.slice(match[0].length);
        if (!first.innerHTML.trim()) first.remove();
        quote.classList.add('callout', `callout-${type}`);
        quote.prepend(createElement('div', 'callout-title', title));
    });
}

function finishDocument(container) {
    renderCallouts(container);
    const prefix = `doc${++docCount}`;
    const headings = [...container.querySelectorAll('h1, h2, h3, h4')];
    headings.forEach((h, i) => h.id = `${prefix}-${i}`);

    container.querySelectorAll('.doc-toc').forEach(toc => {
        const top = Math.min(...headings.map(h => Number(h.tagName[1])));
        headings
            .map(h => ({ h, level: Number(h.tagName[1]) - top }))
            .filter(({ h, level }) => level < TOC_DEPTH && h.textContent.trim() !== 'Table of Contents')
            .forEach(({ h, level }) => {
                const link = createElement('a', `toc-level-${level}`, h.textContent);
                link.href = `#${h.id}`;
                toc.appendChild(link);
            });
    });

    container.querySelectorAll('a[href]').forEach(a => {
        if (!a.getAttribute('href').startsWith('#')) a.target = '_blank';
    });
    container.addEventListener('click', (e) => {
        const link = e.target.closest('a[href^="#"]');
        if (!link) return;
        e.preventDefault();
        scrollToElement(document.getElementById(link.getAttribute('href').slice(1)));
    });

    if (window.Prism) Prism.highlightAllUnder(container);
}

async function renderMarkdown(container, text, path) {
    await loadDocLibraries();
    container.innerHTML = markdownToHtml(text, path);
    finishDocument(container);
}

function joinSource(source) {
    return Array.isArray(source) ? source.join('') : source || '';
}

function stripAnsi(text) {
    return text.replace(/\x1B\[[0-?]*[ -/]*[@-~]/g, '');
}

function notebookCodeText(json) {
    return JSON.parse(json).cells
        .filter(cell => cell.cell_type === 'code')
        .map(cell => joinSource(cell.source))
        .join('\n\n');
}

function renderNotebookOutput(output, basePath) {
    if (output.output_type === 'stream') {
        const text = joinSource(output.text);
        return text.trim() ? createElement('pre', `nb-output nb-${output.name}`, text) : null;
    }
    if (output.output_type === 'error') {
        return createElement('pre', 'nb-output nb-stderr', stripAnsi(output.traceback.join('\n')));
    }

    const data = output.data || {};
    const el = createElement('div', 'nb-output');
    if (data['image/png'] || data['image/jpeg']) {
        const type = data['image/png'] ? 'image/png' : 'image/jpeg';
        const img = createElement('img');
        img.src = `data:${type};base64,${joinSource(data[type]).replace(/\s/g, '')}`;
        el.appendChild(img);
    } else if (data['image/svg+xml'] || data['text/html']) {
        el.innerHTML = joinSource(data['image/svg+xml'] || data['text/html']);
    } else if (data['text/markdown']) {
        el.innerHTML = markdownToHtml(joinSource(data['text/markdown']), basePath);
    } else if (data['text/plain']) {
        return createElement('pre', 'nb-output', stripAnsi(joinSource(data['text/plain'])));
    }
    return el;
}

async function renderNotebook(container, json, path) {
    await loadDocLibraries();
    const notebook = JSON.parse(json);
    const meta = notebook.metadata || {};
    const language = meta.language_info?.name || meta.kernelspec?.language || 'python';

    container.innerHTML = '';
    container.classList.add('notebook');

    notebook.cells.forEach(cell => {
        let source = joinSource(cell.source);
        const cellEl = createElement('div', `nb-cell nb-${cell.cell_type}`);

        if (cell.cell_type === 'markdown') {
            source = source.replace(/attachment:([^)\s]+)/g, (match, name) => {
                const [type, data] = Object.entries(cell.attachments?.[name] || {})[0] || [];
                return type ? `data:${type};base64,${data}` : match;
            });
            cellEl.innerHTML = markdownToHtml(source, path);
        } else if (cell.cell_type === 'code') {
            const prompt = cell.execution_count ? `In [${cell.execution_count}]` : 'In [ ]';
            cellEl.appendChild(createElement('div', 'nb-prompt', prompt));
            const pre = createElement('pre', 'nb-source');
            pre.appendChild(createElement('code', `language-${language}`, source));
            cellEl.appendChild(pre);
            (cell.outputs || [])
                .map(output => renderNotebookOutput(output, path))
                .forEach(el => el && cellEl.appendChild(el));
        } else {
            cellEl.appendChild(createElement('pre', '', source));
        }

        container.appendChild(cellEl);
    });

    finishDocument(container);
}

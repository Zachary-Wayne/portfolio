const PROJECTS_DIR = 'projects';

const TAG_CATEGORIES = {
    'python': 'languages',
    'glsl': 'languages',
    'c++': 'languages',
    'dart': 'languages',
    'clojure': 'languages',
    'powershell': 'languages',
    'opengl': 'frameworks',
    'tkinter': 'frameworks',
    'pytorch': 'frameworks',
    'opencv': 'frameworks',
    'numpy': 'frameworks',
    'flutter': 'frameworks',
    'windows forms': 'frameworks',
    'qiskit': 'frameworks',
    'algorithms': 'topics',
    'functional programming': 'topics',
    'machine learning': 'topics',
    'computer vision': 'topics',
    'shaders': 'topics',
    'audio': 'topics',
    'physics simulation': 'topics',
    'procedural generation': 'topics',
    'game dev': 'types',
    'mobile': 'types',
    'quantum computing': 'topics',
    'automation': 'topics',
    'developer tools': 'types',
    'gui': 'types',
    'cli': 'types',
    'android studio': 'frameworks'
};

const CATEGORY_TITLES = {
    languages: 'Languages',
    frameworks: 'Frameworks & Tools',
    topics: 'Topics',
    types: 'Project Types'
};

const CATEGORY_HUES = {
    languages: 30,
    frameworks: 130,
    topics: 205,
    types: 300
};

const VIDEO_EXTENSIONS = ['mp4', 'webm'];

const PRISM_LANGUAGES = {
    py: 'python',
    md: 'markdown',
    glsl: 'glsl',
    frag: 'glsl',
    vert: 'glsl',
    js: 'javascript',
    html: 'markup',
    css: 'css',
    c: 'c',
    h: 'cpp',
    cc: 'cpp',
    cpp: 'cpp',
    hpp: 'cpp',
    dart: 'dart',
    ps1: 'powershell'
};

const VERT_CODE = `
    attribute vec3 aPosition;
    varying vec2 vTexCoord;
    void main() {
        vec4 pos = vec4(aPosition, 1.0);
        vTexCoord = pos.xy * 0.5 + 0.5;
        gl_Position = pos;
    }
`;

const QUAD_VERTICES = new Float32Array([
    -1, -1, 0,  1, -1, 0, -1,  1, 0,
    -1,  1, 0,  1, -1, 0,  1,  1, 0
]);

let projects = [];
const selectedTags = new Set();
const textCache = new Map();

function fetchText(path) {
    if (!textCache.has(path)) {
        textCache.set(path, fetch(path).then(res => {
            if (!res.ok) throw new Error(`${path}: ${res.status}`);
            return res.text();
        }));
    }
    return textCache.get(path);
}

function projectSections(info) {
    const listed = [].concat(info.section || []);
    if (listed.includes('notes')) return ['notes'];
    return listed.includes('featured') ? ['featured', 'all'] : ['all'];
}

function mediaEntry(base, item) {
    const { src, caption = '' } = typeof item === 'string' ? { src: item } : item;
    return { src: `${base}/${src}`, caption, isVideo: VIDEO_EXTENSIONS.includes(extension(src)) };
}

async function loadProject(folder) {
    const base = `${PROJECTS_DIR}/${folder}`;
    const info = JSON.parse(await fetchText(`${base}/info.json`));
    return {
        id: folder,
        name: info.name || folder,
        description: info.description || '',
        tags: info.tags || [],
        role: info.role || '',
        sections: projectSections(info),
        highlights: info.highlights || [],
        links: info.links || [],
        credits: info.credits || [],
        course: info.course || null,
        labels: info.labels || {},
        shader: info.shader || {},
        files: (info.files || []).map(file => `${base}/${file}`),
        media: (info.media || []).map(item => mediaEntry(base, item)),
        mediaLayout: info.mediaLayout || 'stack',
        preview: info.preview ? mediaEntry(base, info.preview) : null,
        showcase: info.showcase ? mediaEntry(base, info.showcase) : null
    };
}

function stillImage(project) {
    return [project.preview, ...project.media].find(item => item && !item.isVideo) || null;
}

async function loadProjects() {
    const folders = JSON.parse(await fetchText(`${PROJECTS_DIR}/index.json`));
    const results = await Promise.allSettled(folders.map(loadProject));
    results
        .filter(r => r.status === 'rejected')
        .forEach(r => console.error('Failed to load project:', r.reason));
    return results.filter(r => r.status === 'fulfilled').map(r => r.value);
}

function fileName(path) {
    return path.split('/').pop();
}

function extension(path) {
    return path.split('.').pop().toLowerCase();
}

function isShaderProject(project) {
    return ['glsl', 'frag'].includes(extension(project.files[0] || ''));
}

function languageClass(path) {
    return `language-${PRISM_LANGUAGES[extension(path)] || 'clike'}`;
}

function matchesTags(project, tags) {
    return [...tags].every(tag => project.tags.includes(tag));
}

function getCategoryForTag(tag) {
    return TAG_CATEGORIES[tag.toLowerCase()] || 'topics';
}

function stringToHash(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        hash = str.charCodeAt(i) + ((hash << 5) - hash);
    }
    return Math.abs(hash);
}

function applyLabelStyle(element, tag) {
    const hash = stringToHash(tag.toUpperCase());
    const hue = (CATEGORY_HUES[getCategoryForTag(tag)] + (hash % 20) - 10 + 360) % 360;

    element.style.backgroundColor = `hsl(${hue}, ${45 + (hash % 20)}%, ${14 + (hash % 8)}%)`;
    element.style.color = `hsl(${hue}, ${80 + (hash % 15)}%, ${70 + (hash % 15)}%)`;
    element.style.borderColor = `hsl(${hue}, ${55 + (hash % 20)}%, ${30 + (hash % 10)}%)`;
}

function createElement(tag, className, text) {
    const el = document.createElement(tag);
    if (className) el.className = className;
    if (text !== undefined) el.textContent = text;
    return el;
}

function createTagSpan(tag) {
    const span = createElement('span', 'github-label', tag);
    applyLabelStyle(span, tag);
    return span;
}

function createExternalLink(text, url, className = '') {
    const link = createElement('a', className, text);
    link.href = url;
    link.target = '_blank';
    link.rel = 'noopener';
    return link;
}

// The title link on cards and slides opens the project's window, unless a modifier key asks for a new tab.
function createProjectLink(project) {
    const link = createElement('a', 'card-link', project.name);
    link.href = `#${project.id}`;
    link.addEventListener('click', (e) => {
        if (e.ctrlKey || e.metaKey || e.shiftKey) return;
        e.preventDefault();
        openModal(project);
    });
    return link;
}

function isCourseNotes(project) {
    return project.sections[0] === 'notes';
}

function highlightCode(code, text) {
    code.textContent = text;
    if (window.Prism) Prism.highlightElement(code);
}

function createCodeBlock(path) {
    const isNotebook = extension(path) === 'ipynb';
    const pre = document.createElement('pre');
    const code = createElement('code', isNotebook ? 'language-python' : languageClass(path));
    pre.appendChild(code);

    fetchText(path)
        .then(text => highlightCode(code, isNotebook ? notebookCodeText(text) : text))
        .catch(() => highlightCode(code, 'Source file unavailable'));

    return pre;
}

function createFileView(path) {
    const ext = extension(path);
    if (ext !== 'md' && ext !== 'ipynb') {
        const view = createElement('div', 'code-pane');
        view.appendChild(createCodeBlock(path));
        return view;
    }

    const view = createElement('div', 'rendered-doc', 'Loading…');
    const render = ext === 'md' ? renderMarkdown : renderNotebook;
    fetchText(path)
        .then(text => render(view, text, path))
        .catch(err => {
            view.textContent = `Could not display ${fileName(path)}.`;
            console.error(err);
        });
    return view;
}

function createMediaElement({ src, caption, isVideo }, { preview = false, fallback = null } = {}) {
    if (!isVideo) {
        const img = createElement('img');
        img.src = src;
        img.alt = preview ? '' : caption || 'Project output';
        img.loading = 'lazy';
        return img;
    }

    const video = createElement('video');
    video.playsInline = true;
    video.preload = 'metadata';
    if (!preview) {
        video.src = src;
        return withPlayButton(video, src);
    }
    video.src = `${src}#t=1`;
    video.muted = true;
    video.loop = true;
    video.addEventListener('error', () => video.replaceWith(unplayableVideo(src, preview, fallback)), { once: true });
    return video;
}

function withPlayButton(video, src) {
    const frame = createElement('div', 'video-frame');
    const play = createElement('button', 'video-play');
    play.type = 'button';
    play.setAttribute('aria-label', 'Play video');
    play.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 6.5v11l9.2-5.5z" fill="currentColor" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg>';
    frame.append(video, play);
    play.addEventListener('click', () => {
        video.controls = true;
        video.play().catch(() => {});
    });
    video.addEventListener('play', () => { frame.classList.add('is-playing'); });
    video.addEventListener('pause', () => {
        if (!video.seeking) frame.classList.remove('is-playing');
    });
    video.addEventListener('ended', () => { frame.classList.remove('is-playing'); });
    video.addEventListener('error', () => frame.replaceWith(unplayableVideo(src, false, null)), { once: true });
    return frame;
}

function unplayableVideo(src, preview, fallback) {
    if (fallback && !fallback.isVideo) return createMediaElement(fallback, { preview });
    if (preview) return createElement('div', 'video-unsupported');
    const notice = createElement('div', 'video-unsupported');
    notice.appendChild(createElement('p', '', "This browser can't play this video here."));
    notice.appendChild(createExternalLink('Open the video file ↗', src, 'modal-link'));
    return notice;
}

function prefersReducedMotion() {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

function createGlProgram(gl, fragSource) {
    const compile = (type, src) => {
        const shader = gl.createShader(type);
        gl.shaderSource(shader, src);
        gl.compileShader(shader);
        return shader;
    };

    if (!fragSource.includes('precision')) {
        fragSource = 'precision mediump float;\n' + fragSource;
    }

    const vertShader = compile(gl.VERTEX_SHADER, VERT_CODE);
    const fragShader = compile(gl.FRAGMENT_SHADER, fragSource);

    if (!gl.getShaderParameter(fragShader, gl.COMPILE_STATUS)) {
        const error = gl.getShaderInfoLog(fragShader);
        gl.deleteShader(vertShader);
        gl.deleteShader(fragShader);
        return { program: null, error };
    }

    const program = gl.createProgram();
    gl.attachShader(program, vertShader);
    gl.attachShader(program, fragShader);
    gl.linkProgram(program);
    gl.deleteShader(vertShader);
    gl.deleteShader(fragShader);

    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
        const error = gl.getProgramInfoLog(program);
        gl.deleteProgram(program);
        return { program: null, error };
    }

    return { program, error: null };
}

function shaderViewport(canvas, aspect, fit) {
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;
    if (!aspect || !width || !height) return { width, height, left: 0, top: 0 };
    const w = fit === 'cover' ? Math.max(width, height * aspect) : Math.min(width, height * aspect);
    const h = w / aspect;
    return { width: Math.round(w), height: Math.round(h), left: (width - w) / 2, top: (height - h) / 2 };
}

function createShaderRenderer(canvas, { aspect = 0, fit = 'contain', mouseScale = 1 } = {}) {
    const gl = canvas.getContext('webgl');
    if (!gl) return null;
    if (aspect) {
        canvas.style.objectFit = fit;
        canvas.classList.add('fixed-aspect');
    }

    gl.bindBuffer(gl.ARRAY_BUFFER, gl.createBuffer());
    gl.bufferData(gl.ARRAY_BUFFER, QUAD_VERTICES, gl.STATIC_DRAW);

    let program = null;
    let uTime = null;
    let uResolution = null;
    let uMouse = null;
    const startTime = performance.now();

    let mouse = null;
    const pointerTarget = canvas.closest('.project-card') || canvas.parentElement;

    const modal = document.getElementById('project-modal');
    const inModal = Boolean(canvas.closest('.modal-content'));
    let onScreen = true;
    new IntersectionObserver(([entry]) => { onScreen = entry.isIntersecting; }).observe(canvas);
    let compileCount = 0;
    let lastStillFrame = null;
    pointerTarget.addEventListener('pointermove', (e) => {
        const rect = canvas.getBoundingClientRect();
        const view = shaderViewport(canvas, aspect, fit);
        const x = e.clientX - rect.left - view.left;
        const y = view.height - (e.clientY - rect.top - view.top);
        mouse = [view.width / 2 + (x - view.width / 2) * mouseScale, view.height / 2 + (y - view.height / 2) * mouseScale];
    });

    function compile(source) {
        const result = createGlProgram(gl, source);
        if (result.error) return result.error;

        if (program) gl.deleteProgram(program);
        program = result.program;
        gl.useProgram(program);

        const aPosition = gl.getAttribLocation(program, 'aPosition');
        gl.enableVertexAttribArray(aPosition);
        gl.vertexAttribPointer(aPosition, 3, gl.FLOAT, false, 0, 0);

        uTime = gl.getUniformLocation(program, 'uTime') || gl.getUniformLocation(program, 'u_time');
        uResolution = gl.getUniformLocation(program, 'uResolution') || gl.getUniformLocation(program, 'u_resolution');
        uMouse = gl.getUniformLocation(program, 'uMouse') || gl.getUniformLocation(program, 'u_mouse');
        compileCount++;
        return null;
    }

    function frame() {
        if (!canvas.isConnected) {
            gl.getExtension('WEBGL_lose_context')?.loseContext();
            return;
        }

        const { width, height } = shaderViewport(canvas, aspect, fit);
        if (canvas.width !== width || canvas.height !== height) {
            canvas.width = width;
            canvas.height = height;
            gl.viewport(0, 0, width, height);
        }

        const covered = !inModal && modal.classList.contains('active');
        if (program && width && height && onScreen && !covered) {
            const still = prefersReducedMotion();
            const stillFrame = still ? [width, height, mouse, compileCount].join() : null;
            if (!still || stillFrame !== lastStillFrame) {
                if (uTime) gl.uniform1f(uTime, still ? 2 : (performance.now() - startTime) / 1000);
                if (uResolution) gl.uniform2f(uResolution, width, height);
                if (uMouse) gl.uniform2f(uMouse, ...(mouse || [width / 2, height / 2]));
                gl.drawArrays(gl.TRIANGLES, 0, 6);
                lastStillFrame = stillFrame;
            }
        }

        requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);

    return { compile };
}

let searchQuery = [];
let searchVocabulary = [];

function editDistanceTable(string1, string2) {
    const m = string1.length + 1;
    const n = string2.length + 1;
    const dp = Array.from({ length: m }, () => new Array(n).fill(0));

    for (let i = 0; i < m; i++) dp[i][0] = i;
    for (let j = 0; j < n; j++) dp[0][j] = j;

    for (let i = 1; i < m; i++) {
        for (let j = 1; j < n; j++) {
            if (string1[i - 1] === string2[j - 1]) {
                dp[i][j] = dp[i - 1][j - 1];
            } else {
                dp[i][j] = 1 + Math.min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1]);
            }
        }
    }
    return dp;
}

function minimumEditDistance(string1, string2) {
    return editDistanceTable(string1, string2)[string1.length][string2.length];
}

function traceEditPath(dp, string1, string2) {
    const path = new Map([['0,0', 'start']]);
    let i = string1.length;
    let j = string2.length;
    while (i > 0 || j > 0) {
        const key = `${i},${j}`;
        if (i > 0 && j > 0 && string1[i - 1] === string2[j - 1] && dp[i][j] === dp[i - 1][j - 1]) {
            path.set(key, 'match'); i--; j--;
        } else if (i > 0 && j > 0 && dp[i][j] === dp[i - 1][j - 1] + 1) {
            path.set(key, 'substitute'); i--; j--;
        } else if (i > 0 && dp[i][j] === dp[i - 1][j] + 1) {
            path.set(key, 'delete'); i--;
        } else {
            path.set(key, 'insert'); j--;
        }
    }
    return path;
}

function tokenize(text) {
    return text.toLowerCase().match(/[a-z0-9+#]+/g) || [];
}

function buildSearchWords(project) {
    const text = [project.name, project.description, project.role, ...project.tags, ...project.highlights].join(' ');
    return [...new Set(tokenize(text))];
}

function allowedEdits(word) {
    if (word.length <= 3) return 0;
    if (word.length <= 6) return 1;
    return Math.min(5, Math.ceil((word.length - 6) / 2) + 1);
}

function closestWord(query, words) {
    let best = { distance: Infinity, word: '', compared: '' };
    for (const word of words) {
        for (const compared of [word, word.slice(0, query.length)]) {
            const distance = minimumEditDistance(query, compared);
            const wholeWordTie = distance === best.distance && compared === word && best.compared !== best.word;
            if (distance < best.distance || wholeWordTie) best = { distance, word, compared };
        }
        if (best.distance === 0 && best.compared === best.word) break;
    }
    return best;
}

function searchMatch(project) {
    let total = 0;
    const matches = [];
    for (const query of searchQuery) {
        const match = closestWord(query, project.searchWords);
        total += match.distance;
        matches.push({ query, ...match });
    }
    const close = matches.every(m => m.distance <= allowedEdits(m.query));
    return { total, matches, close };
}

function setSearch(text) {
    searchQuery = tokenize(text);
    applyFilter();
    renderSearchPanel();
}

function renderSearchPanel() {
    const panel = document.getElementById('search-panel');
    const summary = document.getElementById('search-panel-summary');
    const grid = document.getElementById('search-panel-table');
    grid.innerHTML = '';

    const query = searchQuery[searchQuery.length - 1];
    if (!query) {
        panel.hidden = true;
        summary.textContent = '';
        return;
    }
    panel.hidden = !panel.dataset.open;

    const { word, compared, distance } = closestWord(query, searchVocabulary);
    const dp = editDistanceTable(query, compared);
    const path = traceEditPath(dp, query, compared);

    const edits = [];
    for (let i = query.length, j = compared.length; i > 0 || j > 0;) {
        const step = path.get(`${i},${j}`);
        if (step === 'substitute') edits.unshift(`“${query[i - 1]}” → “${compared[j - 1]}”`);
        if (step === 'delete') edits.unshift(`remove “${query[i - 1]}”`);
        if (step === 'insert') edits.unshift(`add “${compared[j - 1]}”`);
        if (step !== 'insert') i--;
        if (step !== 'delete') j--;
    }

    const target = compared === word ? `“${word}”` : `the start of “${word}”`;
    const verdict = distance <= allowedEdits(query) ? '' : ` (too far: “${query}” allows ${allowedEdits(query)}, so the nearest projects are shown)`;
    summary.replaceChildren(
        `“${query}” → ${target}: `,
        createElement('strong', '', `${distance} edit${distance === 1 ? '' : 's'}`),
        edits.length ? ` (${edits.join(', ')})` : '',
        verdict
    );

    if (query.length > 14 || compared.length > 16) return;

    const table = createElement('table', 'ed-table');
    const header = table.insertRow();
    ['', 'ε', ...compared].forEach(ch => header.appendChild(createElement('th', '', ch)));
    for (let i = 0; i <= query.length; i++) {
        const row = table.insertRow();
        row.appendChild(createElement('th', '', i === 0 ? 'ε' : query[i - 1]));
        for (let j = 0; j <= compared.length; j++) {
            const cell = row.insertCell();
            cell.textContent = dp[i][j];
            const step = path.get(`${i},${j}`);
            if (step) cell.className = `ed-${step}`;
            if (i === query.length && j === compared.length) cell.classList.add('ed-result');
        }
    }
    grid.appendChild(table);
}

// The header and the nav drop-down each show the full skills list; both are rebuilt so their counts match.
function renderTagFilters() {
    const categorized = {};
    const counts = new Map();
    new Set(projects.flatMap(p => p.tags)).forEach(tag => {
        (categorized[getCategoryForTag(tag)] ??= []).push(tag);
        counts.set(tag, projects.filter(p => matchesTags(p, new Set(selectedTags).add(tag))).length);
    });

    document.querySelectorAll('.skill-groups').forEach(filterContainer => {
        filterContainer.innerHTML = '';

        Object.entries(categorized).forEach(([category, tags]) => {
            const group = createElement('div', 'category-group');
            group.dataset.category = category;
            group.appendChild(createElement('h3', 'category-title', CATEGORY_TITLES[category]));

            const list = createElement('div', 'category-tags');
            tags.forEach(tag => {
                const count = counts.get(tag);

                const btn = createElement('button', 'github-label-btn');
                btn.appendChild(createElement('span', 'tag-text', tag));
                btn.appendChild(createElement('span', 'tag-count', count));

                if (count === 0) {
                    btn.classList.add('disabled');
                    btn.title = `No projects match this with the current filter. Click to show only “${tag}”.`;
                    btn.onclick = () => {
                        selectedTags.clear();
                        toggleTag(tag);
                    };
                } else {
                    applyLabelStyle(btn, tag);
                    btn.classList.toggle('selected', selectedTags.has(tag));
                    btn.setAttribute('aria-pressed', selectedTags.has(tag));
                    btn.onclick = () => toggleTag(tag);
                }
                list.appendChild(btn);
            });

            group.appendChild(list);
            filterContainer.appendChild(group);
        });
    });
}

// The first skill picked in the header jumps to the filtered list; further picks stay put so several can be
// combined without the page moving.
function toggleTag(tag) {
    const first = selectedTags.size === 0;
    if (selectedTags.has(tag)) {
        selectedTags.delete(tag);
    } else {
        selectedTags.add(tag);
    }
    renderTagFilters();
    applyFilter();
    if (first && selectedTags.size > 0) scrollBelowNav(document.getElementById('list-heading'));
}

function applyFilter() {
    const visible = {};
    let count = 0;
    const results = new Map(projects.map(p => [p,
        searchQuery.length ? searchMatch(p) : { total: 0, matches: [], close: true }]));
    const candidates = projects.filter(p => matchesTags(p, selectedTags));
    const nearestOnly = searchQuery.length > 0 && candidates.length > 0
        && !candidates.some(p => results.get(p).close);
    const nearest = Math.min(...candidates.map(p => results.get(p).total));
    projects.forEach(p => {
        const result = results.get(p);
        const match = candidates.includes(p) && (nearestOnly ? result.total === nearest : result.close);
        const fuzzy = match ? result.matches.filter(m => m.distance > 0) : [];
        p.cards.forEach(({ card, badge, section }, i) => {
            card.hidden = !match || (searchQuery.length > 0 && i !== p.cards.length - 1);
            card.style.order = searchQuery.length && match ? result.total : '';
            badge.hidden = fuzzy.length === 0;
            badge.textContent = fuzzy
                .map(m => `≈ ${m.word} · ${m.distance} edit${m.distance === 1 ? '' : 's'}`)
                .join(', ');
            if (match) visible[section] = true;
        });
        if (match) count++;
    });
    arrangeCards(searchQuery.length > 0);
    document.querySelectorAll('.project-section').forEach(section => {
        section.hidden = searchQuery.length
            ? section.dataset.section !== 'results' || count === 0
            : !visible[section.dataset.section];
    });
    document.getElementById('list-heading').textContent = searchQuery.length
        ? `Projects closest matching “${searchQuery.join(' ')}”`
        : 'All projects';
    fitTagRows();

    updateFeatured();
    document.getElementById('no-results').hidden = count > 0;
    document.getElementById('no-results-text').textContent = searchQuery.length
        ? `Nothing matches “${searchQuery.join(' ')}”${selectedTags.size ? ' with the selected tags' : ''}.`
        : 'No projects match the selected tags.';
    document.getElementById('clear-filters').disabled = selectedTags.size === 0 && searchQuery.length === 0;
    document.getElementById('search-status').textContent =
        !searchQuery.length ? ''
        : nearestOnly ? `No close match · nearest ${count === 1 ? 'result' : `${count} results`}`
        : `${count} result${count === 1 ? '' : 's'}`;

    renderSelectedSkills();
}

// The selected skills ride along in the nav bar, so the reader can see what's filtering the list wherever they
// are on the page. Each chip removes its skill; past three, the rest are folded into a "+N" count.
const MAX_NAV_SKILLS = 3;

function renderSelectedSkills() {
    const container = document.getElementById('nav-selected-skills');
    const tags = [...selectedTags];
    container.replaceChildren();
    container.hidden = tags.length === 0;
    tags.slice(0, MAX_NAV_SKILLS).forEach(tag => {
        const chip = createElement('button', 'github-label-btn nav-skill-chip');
        chip.type = 'button';
        chip.title = `Remove “${tag}” from the filter`;
        chip.setAttribute('aria-label', `Remove ${tag} from the filter`);
        chip.append(createElement('span', 'tag-text', tag), createElement('span', 'tag-count', '×'));
        applyLabelStyle(chip, tag);
        chip.addEventListener('click', () => toggleTag(tag));
        container.appendChild(chip);
    });
    if (tags.length > MAX_NAV_SKILLS) {
        const more = createElement('span', 'nav-skill-more', `+${tags.length - MAX_NAV_SKILLS}`);
        more.title = tags.slice(MAX_NAV_SKILLS).join(', ');
        container.appendChild(more);
    }
}

// The carousel is only shown while nothing is filtered. Showing or hiding it moves everything below, so when
// the reader is past the header the page is scrolled by the same amount to keep the project list where it was
// on screen. While the header's skills are in view they stay put instead, so they don't jump from the pointer.
function updateFeatured() {
    const featured = document.getElementById('featured');
    const hidden = searchQuery.length > 0 || selectedTags.size > 0 || !projects.some(p => p.sections.includes('featured'));
    if (featured.hidden === hidden) return;

    const main = document.getElementById('main');
    const before = main.getBoundingClientRect().top;
    const headerInView = document.querySelector('.navbar-brand').getBoundingClientRect().bottom > 0;
    featured.hidden = hidden;
    if (!hidden) fitShowcase();
    if (!headerInView) window.scrollBy({ top: main.getBoundingClientRect().top - before, behavior: 'instant' });
}

function fitTagRows() {
    const listView = document.body.classList.contains('view-list');
    document.querySelectorAll('.project-card:not([hidden]) .tags-container').forEach(container => {
        const tags = [...container.querySelectorAll('.github-label:not(.tag-more)')];
        let more = container.querySelector('.tag-more');
        tags.forEach(tag => { tag.hidden = false; });
        if (more) more.hidden = true;
        if (!listView || tags.length === 0) return;

        const rowTop = tags[0].offsetTop;
        const overflow = tags.filter(tag => tag.offsetTop > rowTop);
        if (overflow.length === 0) return;

        if (!more) {
            more = createElement('span', 'github-label tag-more');
            container.appendChild(more);
        }
        more.hidden = false;
        const offRow = () => more.offsetTop > rowTop || tags.some(t => !t.hidden && t.offsetTop > rowTop);
        let hiddenCount = 0;
        for (let i = tags.length - 1; i > 0 && offRow(); i--) {
            tags[i].hidden = true;
            hiddenCount++;
            more.textContent = `+${hiddenCount}`;
        }
        more.title = tags.filter(t => t.hidden).map(t => t.textContent).join(', ');
    });
}

function clearFilters({ alsoSearch = false } = {}) {
    selectedTags.clear();
    renderTagFilters();
    if (alsoSearch) {
        document.getElementById('search').value = '';
        setSearch('');
    } else {
        applyFilter();
    }
}

function renderCardPreview(container, project) {
    if (isCourseNotes(project) && extension(project.files[0] || '') === 'md') {
        renderNotePreview(container, project.files[0]);
    } else if (isShaderProject(project)) {
        const canvas = document.createElement('canvas');
        container.appendChild(canvas);
        const renderer = createShaderRenderer(canvas, { ...project.shader, fit: 'cover' });
        if (renderer) fetchText(project.files[0]).then(renderer.compile).catch(() => {});
    } else if (project.preview || project.media.length > 0) {
        const media = createMediaElement(project.preview || project.media[0], { preview: true, fallback: stillImage(project) });
        container.appendChild(media);
        if (media.tagName === 'VIDEO') {
            const card = container.closest('.project-card');
            card.addEventListener('mouseenter', () => media.play().catch(() => {}));
            card.addEventListener('mouseleave', () => media.pause());
        }
    } else if (project.files.length > 0) {
        const codeFile = project.files.find(f => extension(f) !== 'md') || project.files[0];
        container.appendChild(createCodeBlock(codeFile));
    }
}

const notePreviewObserver = new IntersectionObserver(entries => {
    entries.filter(entry => entry.isIntersecting).forEach(entry => {
        notePreviewObserver.unobserve(entry.target);
        const { path } = entry.target.dataset;
        fetchText(path)
            .then(text => renderMarkdown(entry.target, text, path))
            .catch(() => { entry.target.textContent = ''; });
    });
}, { rootMargin: '400px 0px' });

function renderNotePreview(container, path) {
    const doc = createElement('div', 'rendered-doc card-doc-preview');
    doc.dataset.path = path;
    container.appendChild(doc);
    notePreviewObserver.observe(doc);
}

function createCornerBadge(project, seed) {
    const featured = project.sections.includes('featured');
    if (!featured && !isCourseNotes(project)) return null;
    const label = featured ? 'Featured project' : 'Course notes';
    const badge = createElement('span', featured ? 'card-ribbon' : 'card-fold');
    if (featured) badge.style.setProperty('--glint-delay', `${(stringToHash(seed) % 40) / 10}s`);
    badge.title = label;
    badge.setAttribute('role', 'img');
    badge.setAttribute('aria-label', label);
    return badge;
}

function createCard(project, section) {
    const card = createElement('article', 'project-card');

    const title = createElement('h3', 'card-title');
    title.appendChild(createProjectLink(project));

    card.addEventListener('click', (e) => {
        if (e.target.closest('a')) return;
        if (window.getSelection().toString()) return;
        openModal(project);
    });

    const preview = createElement('div', 'card-bg-container');
    preview.inert = true;
    preview.setAttribute('aria-hidden', 'true');
    const tags = createElement('div', 'tags-container');
    project.tags.forEach(t => tags.appendChild(createTagSpan(t)));
    const corner = createCornerBadge(project, project.id + section);
    if (corner) card.appendChild(corner);
    const badge = createElement('span', 'card-match');
    badge.hidden = true;
    const cta = createElement('span', 'card-cta', isCourseNotes(project) ? 'Read notes' : 'View project');
    cta.setAttribute('aria-hidden', 'true');

    card.append(preview, title);
    if (project.role) {
        const role = createElement('p', 'card-role', project.role);
        role.title = project.role;
        card.appendChild(role);
    }
    card.append(tags, createElement('div', 'card-description-text', project.description), badge, cta);
    return { card, preview, badge, section };
}

function renderProjects() {
    searchLayout = false;
    const grids = {};
    document.querySelectorAll('.project-section').forEach(section => {
        grids[section.dataset.section] = section.querySelector('.projects-grid');
        grids[section.dataset.section].innerHTML = '';
    });

    projects.forEach(project => {
        project.cards = project.sections.filter(section => grids[section]).map(section => {
            const entry = createCard(project, section);
            grids[entry.section].appendChild(entry.card);
            renderCardPreview(entry.preview, project);
            return entry;
        });
    });
}

function renderShowcase() {
    const showcase = document.getElementById('featured');
    const track = showcase.querySelector('.showcase-track');
    const dots = showcase.querySelector('.showcase-dots');
    const count = showcase.querySelector('.showcase-count');
    const featured = projects.filter(p => p.sections.includes('featured'));
    track.innerHTML = '';
    dots.innerHTML = '';
    showcase.hidden = featured.length === 0;
    if (featured.length === 0) return;

    const rail = createElement('div', 'showcase-rail');
    track.appendChild(rail);
    const slides = featured.map((project, i) => {
        const slide = createSlide(project, i, featured.length);
        rail.appendChild(slide);
        const dot = createElement('button', 'showcase-dot');
        dot.type = 'button';
        dot.setAttribute('aria-label', `Show ${project.name}`);
        dot.addEventListener('click', () => goTo(i));
        dots.appendChild(dot);
        return slide;
    });

    const last = slides.length - 1;
    const still = () => prefersReducedMotion();
    let pos = 0;
    let target = 0;
    let active = -1;

    const slideWidth = () => parseFloat(getComputedStyle(slides[0]).width);
    const step = () => slideWidth() + parseFloat(getComputedStyle(rail).columnGap || 0);
    const clampIndex = (i) => Math.max(0, Math.min(last, i));
    const wrapIndex = (i) => (i + slides.length) % slides.length;

    function edgeResist(p) {
        if (p < 0) return -0.25 * (1 - 1 / (1 - p));
        if (p > last) return last + 0.25 * (1 - 1 / (1 + p - last));
        return p;
    }

    function render() {
        const width = slideWidth();
        const stepPx = width + parseFloat(getComputedStyle(rail).columnGap || 0);
        const x = track.getBoundingClientRect().width / 2 - width / 2 - pos * stepPx;
        rail.style.transform = `translate3d(${x}px, 0, 0)`;
        slides.forEach((slide, i) => {
            const d = i - pos;
            slide.style.setProperty('--offset', `${d * stepPx}px`);
            const a = Math.min(Math.abs(d), 1.5);
            slide.style.setProperty('--turn', still() ? '0deg' : `${Math.max(-1.2, Math.min(1.2, d)) * -32}deg`);
            slide.style.setProperty('--shrink', still() ? 1 : 1 - a * 0.1);
            slide.style.setProperty('--fade', 1 - Math.min(a, 1) * 0.55);
        });
        const nearest = clampIndex(Math.round(pos));
        if (nearest === active) return;
        active = nearest;
        slides.forEach((slide, i) => {
            const on = i === active;
            slide.classList.toggle('is-active', on);
            slide.setAttribute('aria-hidden', String(!on));
            slide.querySelectorAll('a, button').forEach(el => { el.tabIndex = on ? 0 : -1; });
        });
        syncVideos();
        [...dots.children].forEach((dot, i) => dot.setAttribute('aria-current', String(i === active)));
        count.textContent = `${active + 1} / ${slides.length}`;
    }

    function syncVideos() {
        slides.forEach((slide, i) => {
            const video = slide.querySelector('.showcase-media video');
            if (!video) return;
            if (track.clientWidth && Math.abs(i - active) <= 2 && !still()) video.play().catch(() => {});
            else video.pause();
        });
    }

    let anim = 0;
    let velocity = 0;
    function stop() {
        cancelAnimationFrame(anim);
        anim = 0;
    }

    function goTo(i, smooth = true, initialVelocity = 0) {
        target = clampIndex(i);
        stop();
        if (!smooth || still()) {
            pos = target;
            velocity = 0;
            render();
            return;
        }
        const stiffness = 160;
        const damping = 2 * Math.sqrt(stiffness);
        velocity = Math.max(-6, Math.min(6, initialVelocity));
        let then = performance.now();
        const frame = (now) => {
            const dt = Math.min(0.032, (now - then) / 1000);
            then = now;
            velocity += (-stiffness * (pos - target) - damping * velocity) * dt;
            pos += velocity * dt;
            if (Math.abs(pos - target) < 0.0005 && Math.abs(velocity) < 0.01) {
                pos = target;
                velocity = 0;
                anim = 0;
            } else {
                anim = requestAnimationFrame(frame);
            }
            render();
        };
        anim = requestAnimationFrame(frame);
    }

    function settle(from, speed = 0) {
        const moved = (pos - from) * step();
        let dest = Math.round(pos);
        if (dest === from) {
            if (Math.abs(moved) > Math.min(60, step() / 8)) dest = from + Math.sign(moved);
            else if (Math.abs(speed) * step() > 400) dest = from + Math.sign(speed);
        }
        goTo(dest, true, speed);
    }

    showcase.querySelectorAll('.showcase-arrow').forEach(btn => {
        btn.addEventListener('click', () => goTo(wrapIndex(target + Number(btn.dataset.step))));
    });
    track.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
            e.preventDefault();
            goTo(wrapIndex(target + (e.key === 'ArrowRight' ? 1 : -1)));
        }
    });
    new ResizeObserver(() => {
        if (track.clientWidth) render();
        syncVideos();
    }).observe(track);

    // Trackpad swipes never drag the carousel part-way (which could look like a flip and then spring back): nothing
    // moves until a swipe has gone far enough sideways to mean "next" or "previous", then it turns one whole slide
    // with the usual spring. One swipe turns at most one slide; the rest of it, momentum included, is ignored
    // until the trackpad has been still for a moment.
    const SWIPE_DISTANCE = 24;
    let wheel = null;
    let lastTurned = { t: -Infinity, size: 0 };  // the last event of a swipe that turned the carousel
    track.addEventListener('wheel', (e) => {
        const scale = e.deltaMode === 1 ? 40 : e.deltaMode === 2 ? track.clientWidth : 1;
        const dx = (e.shiftKey && !e.deltaX ? e.deltaY : e.deltaX) * scale;
        const dy = e.shiftKey ? 0 : e.deltaY * scale;
        // A vertical scroll only turns into a swipe on a strong, clearly sideways movement, so wobble as it slows
        // can't hijack it. Once a swipe has turned the carousel, clearly vertical movement goes back to the page
        // instead of being swallowed until the trackpad's momentum dies down.
        if (wheel?.axis === 'y' && Math.abs(dx) >= 8 && Math.abs(dx) > Math.abs(dy) * 3) {
            clearTimeout(wheel.quiet);
            wheel = null;
        } else if (wheel?.axis === 'x' && wheel.done && Math.abs(dy) >= 4 && Math.abs(dy) > Math.abs(dx) * 2) {
            clearTimeout(wheel.quiet);
            wheel = { axis: 'y' };
        }
        // The first events of a swipe are only a pixel or two, so the direction is decided once it has moved 6 px.
        // Within 45° of horizontal counts as sideways, and a sideways swipe stays sideways until it ends, however
        // much it drifts vertically.
        if (!wheel) wheel = { axis: '?', sx: 0, sy: 0, first: Math.abs(dx), start: e.timeStamp };
        let moveX = dx;
        if (wheel.axis === '?') {
            wheel.sx += dx;
            wheel.sy += dy;
            if (Math.hypot(wheel.sx, wheel.sy) >= 6) {
                if (Math.abs(wheel.sx) > Math.abs(wheel.sy)) {
                    // A busy moment can delay events past the 140 ms gap, so a swipe that already turned the
                    // carousel can resume as if it were new. It carries on at about the speed it had, whereas a new
                    // swipe after the old one's momentum has died down starts far faster than that slow tail.
                    const continuing = wheel.start - lastTurned.t < 300 && wheel.first <= lastTurned.size * 1.5 + 2;
                    Object.assign(wheel, { axis: 'x', travel: 0, done: continuing, recent: [wheel.first], slowest: Infinity });
                    moveX = wheel.sx;
                } else {
                    wheel.axis = 'y';
                }
            }
        }
        const gesture = wheel;
        clearTimeout(gesture.quiet);
        gesture.quiet = setTimeout(() => {
            if (wheel === gesture) wheel = null;
        }, 140);
        if (gesture.axis !== 'x') return;
        e.preventDefault();
        const size = Math.abs(moveX);
        if (gesture.done) {
            lastTurned = { t: e.timeStamp, size };
            // Momentum after a swipe only slows down, though single events jitter (they arrive at uneven intervals).
            // When the movement over the last three events climbs well above its slowest, a new swipe has started
            // before the momentum ended, so it can turn again.
            gesture.recent = [...gesture.recent, size].slice(-3);
            if (gesture.recent.length < 3) return;
            const recent = gesture.recent.reduce((a, b) => a + b, 0);
            gesture.slowest = Math.min(gesture.slowest, recent);
            if (recent < gesture.slowest * 1.8 + 12) return;
            Object.assign(gesture, { done: false, travel: 0 });
        }

        gesture.travel += moveX;
        if (Math.abs(gesture.travel) >= SWIPE_DISTANCE) {
            Object.assign(gesture, { done: true, recent: [size], slowest: Infinity });
            lastTurned = { t: e.timeStamp, size };
            const from = anim ? target : clampIndex(Math.round(pos));
            goTo(from + Math.sign(gesture.travel));
        }
    }, { passive: false });

    let drag = null;
    track.addEventListener('pointerdown', (e) => {
        if (e.pointerType === 'mouse' && e.button !== 0) return;
        drag = { id: e.pointerId, x: e.clientX, y: e.clientY, moving: false, samples: [] };
    });
    track.addEventListener('pointermove', (e) => {
        if (!drag || e.pointerId !== drag.id) return;
        const dx = e.clientX - drag.x;
        const dy = e.clientY - drag.y;
        if (!drag.moving) {
            if (Math.abs(dy) > 8 && Math.abs(dy) > Math.abs(dx)) {
                drag = null;
                return;
            }
            if (Math.abs(dx) < 8) return;
            stop();
            drag.moving = true;
            drag.x = e.clientX;
            drag.start = pos;
            drag.from = clampIndex(Math.round(pos));
            track.setPointerCapture(e.pointerId);
            track.classList.add('is-dragging');
        }
        drag.samples.push({ x: e.clientX, t: e.timeStamp });
        if (drag.samples.length > 5) drag.samples.shift();
        pos = edgeResist(drag.start - (e.clientX - drag.x) / step());
        render();
    });
    const endDrag = (e) => {
        if (!drag || e.pointerId !== drag.id) return;
        const { moving, samples, from } = drag;
        drag = null;
        if (!moving) return;
        track.classList.remove('is-dragging');
        const first = samples[0];
        const latest = samples[samples.length - 1];
        const fresh = first && latest.t > first.t && e.timeStamp - latest.t < 80;
        settle(from, fresh ? (first.x - latest.x) / (latest.t - first.t) * 1000 / step() : 0);
        const swallow = (ev) => {
            ev.stopPropagation();
            ev.preventDefault();
        };
        track.addEventListener('click', swallow, { capture: true, once: true });
        setTimeout(() => track.removeEventListener('click', swallow, { capture: true }), 0);
    };
    track.addEventListener('pointerup', endDrag);
    track.addEventListener('pointercancel', endDrag);

    track.addEventListener('click', (e) => {
        const slide = e.target.closest('.showcase-slide');
        if (!slide || e.target.closest('a, button')) return;
        const i = slides.indexOf(slide);
        if (i !== active) goTo(i);
        else openModal(featured[i]);
    });

    requestAnimationFrame(() => goTo(0, false));
}

// Caps the carousel's slides to the room left on the first screen, so a visitor sees the whole slide without
// scrolling. Slides whose text doesn't fit drop their bullet points, then cut the description to three lines.
// Only for side-by-side slides; on short screens (under 300 px of room) and stacked layouts the page scrolls.
function fitShowcase() {
    const showcase = document.getElementById('featured');
    const slides = [...showcase.querySelectorAll('.showcase-slide')];
    slides.forEach(slide => slide.classList.remove('fit-tight', 'fit-tighter'));
    showcase.style.removeProperty('--slide-fit');
    if (showcase.hidden || slides.length === 0 || !window.matchMedia('(min-width: 1101px)').matches) return;

    const track = showcase.querySelector('.showcase-track');
    const trackStyle = getComputedStyle(track);
    const top = track.getBoundingClientRect().top + window.scrollY + parseFloat(trackStyle.paddingTop);
    const below = parseFloat(trackStyle.paddingBottom) + showcase.querySelector('.showcase-dots').offsetHeight + 16;
    const fit = Math.floor(window.innerHeight - top - below);
    if (fit < 300) return;
    showcase.style.setProperty('--slide-fit', `${fit}px`);
    slides.forEach(slide => {
        const info = slide.querySelector('.showcase-info');
        for (const level of ['fit-tight', 'fit-tighter']) {
            if (info.scrollHeight <= info.clientHeight + 1) break;
            slide.classList.add(level);
        }
    });
}

function createSlide(project, index, total) {
    const slide = createElement('article', 'showcase-slide');
    slide.setAttribute('aria-roledescription', 'slide');
    slide.setAttribute('aria-label', `${index + 1} of ${total}: ${project.name}`);

    const media = createElement('div', 'showcase-media');
    media.setAttribute('aria-hidden', 'true');
    media.inert = true;
    const item = project.showcase || project.preview || project.media[0];
    if (item && !isShaderProject(project)) {
        media.appendChild(createMediaElement(item, { preview: true, fallback: stillImage(project) }));
    } else {
        renderCardPreview(media, project);
    }

    const info = createElement('div', 'showcase-info');
    if (project.role) {
        const role = createElement('p', 'showcase-role', project.role);
        role.title = project.role;
        info.appendChild(role);
    }
    const title = createElement('h3', 'showcase-title');
    title.appendChild(createProjectLink(project));
    const tags = createElement('div', 'tags-container');
    project.tags.forEach(t => tags.appendChild(createTagSpan(t)));
    info.append(title, tags, createElement('p', 'showcase-description', project.description));

    if (project.highlights.length > 0) {
        const list = createElement('ul', 'showcase-highlights');
        project.highlights.slice(0, 3).forEach(h => list.appendChild(createElement('li', '', h)));
        info.appendChild(list);
    }

    const actions = createElement('div', 'showcase-actions');
    const open = createElement('button', 'showcase-open', 'View project →');
    open.type = 'button';
    open.addEventListener('click', () => openModal(project));
    actions.appendChild(open);
    project.links.forEach(({ label, url }) => actions.appendChild(createExternalLink(`${label} ↗`, url, 'modal-link')));
    info.appendChild(actions);

    slide.append(media, info);
    return slide;
}

let searchLayout = false;

function arrangeCards(searching) {
    if (searching === searchLayout) return;
    searchLayout = searching;
    const results = document.querySelector('#search-results .projects-grid');
    projects.forEach(project => {
        project.cards.forEach((entry, i) => {
            const home = document.querySelector(`.project-section[data-section="${entry.section}"] .projects-grid`);
            const searchCard = searching && i === project.cards.length - 1;
            (searchCard ? results : home).appendChild(entry.card);
        });
    });
}

let focusBeforeModal = null;

let modalProject = null;

// The projects in the order their cards appear on screen. Search results are ranked with CSS `order` rather than
// moved in the DOM, so cards sharing a grid are compared by that first.
function modalSequence() {
    const shownBefore = (a, b) => {
        if (a.parentElement === b.parentElement) {
            const byOrder = (Number(a.style.order) || 0) - (Number(b.style.order) || 0);
            if (byOrder) return byOrder;
        }
        return a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING ? -1 : 1;
    };
    const visible = projects
        .flatMap(project => project.cards.filter(({ card }) => !card.hidden && !card.closest('[hidden]')).map(({ card }) => ({ project, card })))
        .sort((a, b) => shownBefore(a.card, b.card))
        .map(({ project }) => project)
        .filter((project, i, list) => list.indexOf(project) === i);
    return visible.includes(modalProject) ? visible : projects;
}

// The previous or next project in the list as it's currently shown, or null at either end: the arrows stop
// there rather than wrapping, so a filter that leaves one or two projects doesn't point back at the same ones.
function neighbourProject(step) {
    const sequence = modalSequence();
    return sequence[sequence.indexOf(modalProject) + step] || null;
}

function stepModal(step, focusTarget) {
    const other = modalProject && neighbourProject(step);
    if (other) openModal(other, { focusTarget });
}

function openModal(project, { focusTarget = null } = {}) {
    const modal = document.getElementById('project-modal');
    if (!modal.classList.contains('active')) focusBeforeModal = document.activeElement;
    modalProject = project;

    document.getElementById('modal-title').textContent = project.name;
    document.getElementById('modal-role').textContent = project.role;

    const tags = document.getElementById('modal-tags');
    tags.innerHTML = '';
    project.tags.forEach(t => tags.appendChild(createTagSpan(t)));

    document.getElementById('modal-links').replaceChildren(
        ...project.links.map(({ label, url }) => createExternalLink(`${label} ↗`, url, 'modal-link')));

    const description = document.getElementById('modal-description');
    description.innerHTML = '';
    description.appendChild(createElement('p', '', project.description));
    if (project.highlights.length > 0) {
        const list = createElement('ul', 'modal-highlights');
        project.highlights.forEach(h => list.appendChild(createElement('li', '', h)));
        description.appendChild(list);
    }
    project.credits.forEach(({ label, text, url, note }) => {
        const line = createElement('p', 'modal-credit');
        line.appendChild(createElement('strong', '', `${label}: `));
        line.append(url ? createExternalLink(text, url) : text);
        if (note) line.append(` (${note})`);
        description.appendChild(line);
    });
    if (project.course) {
        const { name, professor, url } = project.course;
        const subject = isCourseNotes(project) ? 'These notes were' : 'The project was';
        const line = createElement('p', 'modal-credit', `${subject} part of ${name} taught by `);
        line.append(createExternalLink(professor, url), '.');
        description.appendChild(line);
    }

    const corner = createCornerBadge(project, project.id);
    document.getElementById('modal-corner').replaceChildren(...(corner ? [corner] : []));

    const body = document.getElementById('modal-body-container');
    body.innerHTML = '';
    delete body.dataset.toc;

    if (isShaderProject(project)) {
        renderShaderModal(body, project);
    } else {
        renderDocumentModal(body, project);
    }

    document.querySelector('.modal-scroll').scrollTop = 0;
    renderModalToc();
    updateScrollHint();
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
    history.replaceState(null, '', `#${project.id}`);
    modal.querySelectorAll('.modal-nav').forEach(button => {
        const step = Number(button.dataset.step);
        const other = neighbourProject(step);
        button.hidden = !other;
        if (!other) return;
        const label = `${step < 0 ? 'Previous' : 'Next'}: ${other.name}`;
        button.querySelector('.modal-nav-label').textContent = label;
        button.setAttribute('aria-label', label);
    });
    // Stepping onto the last project hides the arrow that was used, so focus moves to the close button instead.
    (focusTarget && !focusTarget.hidden ? focusTarget : modal.querySelector('.modal-close')).focus();
}

function createPane(title) {
    const pane = createElement('section', 'modal-pane');
    if (title) pane.appendChild(createElement('div', 'pane-header', title));
    return pane;
}

function renderDocumentModal(body, project) {
    body.className = 'modal-body document-view';

    if (project.media.length > 0) {
        const label = project.labels.media || 'Preview';
        const pane = createPane(label);
        pane.dataset.toc = label;
        pane.classList.toggle('output-grid', project.mediaLayout === 'grid');
        project.media.forEach(item => {
            const figure = createElement('figure', item.isVideo ? 'output-figure is-video' : 'output-figure');
            const media = createMediaElement(item);
            if (item.isVideo) {
                figure.appendChild(media);
            } else {
                const link = createElement('a');
                link.href = item.src;
                link.target = '_blank';
                link.title = 'Open full size';
                link.appendChild(media);
                figure.appendChild(link);
            }
            if (item.caption) figure.appendChild(createElement('figcaption', '', item.caption));
            pane.appendChild(figure);
        });
        if (project.mediaLayout === 'grid') {
            let run = [];
            [...pane.querySelectorAll('.output-figure'), null].forEach(figure => {
                if (figure && !figure.classList.contains('is-video')) return run.push(figure);
                if (run.length % 2) run[run.length - 1].classList.add('is-wide');
                run = [];
            });
        }
        body.appendChild(pane);
    }

    if (project.files.length > 0) {
        body.appendChild(createFileTabs(project.files, filesLabel(project, project.files)));
    }

    if (body.children.length === 0) {
        body.appendChild(createElement('p', 'modal-empty', 'No files for this project yet.'));
    }
}

// What the modal calls a project's files: its own "labels.files" if set, otherwise a name from the file types.
function filesLabel(project, files) {
    if (project.labels.files) return project.labels.files;
    if (isCourseNotes(project)) return 'Notes';
    const documents = files.filter(path => ['md', 'ipynb'].includes(extension(path))).length;
    if (documents === 0) return 'Source code';
    if (documents === files.length) return files.length === 1 ? 'Document' : 'Documents';
    return 'Docs & source';
}

function createFileTabs(files, label) {
    const pane = createPane();
    pane.dataset.toc = label;
    const tabBar = createElement('div', 'pane-tabs');
    tabBar.setAttribute('role', 'tablist');
    pane.appendChild(tabBar);

    const tabs = files.map(path => {
        const tab = createElement('button', 'pane-tab', fileName(path));
        tab.setAttribute('role', 'tab');
        tab.title = fileName(path);
        const panel = createFileView(path);
        panel.setAttribute('role', 'tabpanel');
        tabBar.appendChild(tab);
        pane.appendChild(panel);
        return { tab, panel };
    });

    const select = (selected) => tabs.forEach(({ tab, panel }) => {
        const active = tab === selected;
        tab.classList.toggle('active', active);
        tab.setAttribute('aria-selected', active);
        tab.tabIndex = active ? 0 : -1;
        panel.hidden = !active;
    });
    tabs.forEach(({ tab }) => tab.onclick = () => select(tab));
    select(tabs[0].tab);

    tabBar.onkeydown = (e) => {
        const step = { ArrowRight: 1, ArrowLeft: -1 }[e.key];
        if (!step) return;
        const current = tabs.findIndex(({ tab }) => tab === document.activeElement);
        const next = tabs[(current + step + tabs.length) % tabs.length].tab;
        select(next);
        next.focus();
        e.preventDefault();
    };

    return pane;
}

function renderShaderModal(body, project) {
    const extraFiles = project.files.slice(1);
    let stage = body;
    if (extraFiles.length === 0) {
        body.className = 'modal-body shader-view';
        body.dataset.toc = 'Live preview';
    } else {
        body.className = 'modal-body document-view';
        const pane = createPane('Live preview · move the mouse to look around');
        pane.dataset.toc = 'Live preview';
        stage = createElement('div', 'shader-view shader-stage');
        pane.appendChild(stage);
        body.appendChild(pane);
        body.appendChild(createFileTabs(extraFiles, filesLabel(project, extraFiles)));
    }
    renderShaderStage(stage, project.files[0], { collapsed: extraFiles.length > 0, options: project.shader });
}

function renderShaderStage(stage, shaderPath, { collapsed = false, options = {} } = {}) {
    const canvas = document.createElement('canvas');
    const editor = createElement('div', 'shader-editor');
    const header = createElement('div', 'shader-editor-header');
    const toggleBtn = createElement('button', 'shader-toggle-btn', 'Hide');
    const code = createElement('div', 'shader-code');
    const highlight = createElement('pre', 'shader-highlight');
    const highlighted = createElement('code', 'language-glsl');
    const textarea = createElement('textarea', 'shader-textarea');
    const errorLog = createElement('div', 'shader-error-log');
    textarea.spellcheck = false;
    textarea.setAttribute('aria-label', `${fileName(shaderPath)} source (editable)`);
    highlight.setAttribute('aria-hidden', 'true');
    highlight.appendChild(highlighted);
    code.append(highlight, textarea);

    header.appendChild(createElement('span', '', fileName(shaderPath)));
    header.appendChild(toggleBtn);
    editor.appendChild(header);
    editor.appendChild(code);
    editor.appendChild(errorLog);

    const paint = () => {
        highlighted.textContent = `${textarea.value}\n`;
        if (window.Prism) Prism.highlightElement(highlighted);
        syncScroll();
    };
    const syncScroll = () => {
        highlight.scrollTop = textarea.scrollTop;
        highlight.scrollLeft = textarea.scrollLeft;
    };
    textarea.addEventListener('scroll', syncScroll);
    stage.appendChild(canvas);
    stage.appendChild(editor);

    const setCollapsed = (value) => {
        editor.classList.toggle('collapsed', value);
        toggleBtn.textContent = value ? 'Show Code' : 'Hide';
    };
    setCollapsed(collapsed);
    toggleBtn.onclick = () => setCollapsed(!editor.classList.contains('collapsed'));

    const renderer = createShaderRenderer(canvas, { ...options, fit: 'contain' });
    if (!renderer) return;

    const compile = () => {
        const error = renderer.compile(textarea.value);
        errorLog.textContent = error || '';
        errorLog.hidden = !error;
    };

    textarea.oninput = () => {
        paint();
        compile();
    };
    textarea.onkeydown = (e) => {
        if (e.key !== 'Tab') return;
        e.preventDefault();
        textarea.setRangeText('    ', textarea.selectionStart, textarea.selectionEnd, 'end');
        paint();
        compile();
    };

    fetchText(shaderPath)
        .then(source => {
            textarea.value = source;
            paint();
            compile();
        })
        .catch(() => {
            textarea.value = '// Source file unavailable';
            paint();
        });
}

function closeModal() {
    const modal = document.getElementById('project-modal');
    if (!modal.classList.contains('active')) return;
    modal.classList.remove('active');
    modalProject = null;
    document.getElementById('modal-body-container').innerHTML = '';
    document.body.style.overflow = '';
    history.replaceState(null, '', location.pathname + location.search);
    focusBeforeModal?.focus();
}

function syncModalToHash() {
    const id = decodeURIComponent(location.hash.slice(1));
    const project = projects.find(p => p.id === id);
    if (project) openModal(project);
    else closeModal();
}

function trapFocus(e, modal) {
    if (e.key !== 'Tab') return;
    const focusable = [...modal.querySelectorAll('button, a[href], textarea, video[controls], [tabindex="0"]')]
        .filter(el => el.offsetParent !== null);
    if (focusable.length === 0) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (e.shiftKey && document.activeElement === first) {
        last.focus();
        e.preventDefault();
    } else if (!e.shiftKey && document.activeElement === last) {
        first.focus();
        e.preventDefault();
    }
}

function stickyHeight() {
    return document.querySelector('.site-nav').offsetHeight + document.getElementById('toolbar').offsetHeight;
}

function scrollToSection(section) {
    window.scrollTo({ top: section.getBoundingClientRect().top + window.scrollY - stickyHeight() - 12, behavior: 'smooth' });
}

// Like scrollToSection, but for targets above the sticky toolbar. The nav is measured now rather than through
// --nav-h, which lags a frame behind the nav growing a row for the selected-skill chips.
function scrollBelowNav(target) {
    const navHeight = document.querySelector('.site-nav').offsetHeight;
    window.scrollTo({ top: target.getBoundingClientRect().top + window.scrollY - navHeight - 12, behavior: 'smooth' });
}

function trackStickyHeights() {
    const nav = document.querySelector('.site-nav');
    const toolbar = document.getElementById('toolbar');
    const root = document.documentElement.style;
    const measure = () => {
        root.setProperty('--nav-h', `${Math.floor(nav.getBoundingClientRect().height)}px`);
        root.setProperty('--toolbar-h', `${Math.ceil(toolbar.getBoundingClientRect().height)}px`);
    };
    const observer = new ResizeObserver(measure);
    observer.observe(nav);
    observer.observe(toolbar);
    new ResizeObserver(() => root.setProperty('--page-w', `${document.documentElement.clientWidth}px`)).observe(document.documentElement);
}

function initNav() {
    const nav = document.querySelector('.site-nav');
    document.querySelector('.nav-brand').addEventListener('click', (e) => {
        e.preventDefault();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });

    const heading = document.querySelector('.navbar-brand h1');
    const updateBrand = () => {
        nav.classList.toggle('show-brand', heading.getBoundingClientRect().bottom < nav.offsetHeight);
    };
    window.addEventListener('scroll', updateBrand, { passive: true });
    updateBrand();

    const panel = document.getElementById('search-panel');
    const setPanelOpen = (open) => {
        if (open) panel.dataset.open = 'true';
        else delete panel.dataset.open;
        panel.hidden = !open || searchQuery.length === 0;
    };
    const searchBox = document.querySelector('.nav-search');
    searchBox.addEventListener('focusin', () => setPanelOpen(true));
    searchBox.addEventListener('focusout', (e) => {
        if (!searchBox.contains(e.relatedTarget)) setPanelOpen(false);
    });
    document.getElementById('search-panel-note').addEventListener('click', (e) => {
        e.preventDefault();
        setPanelOpen(false);
        const note = projects.find(p => p.id === 'note_edit_distance');
        if (note) openModal(note);
    });

    const search = document.getElementById('search');
    search.addEventListener('input', () => {
        setSearch(search.value);
        const main = document.querySelector('.main-content');
        if (search.value && main.getBoundingClientRect().top < 0) scrollToSection(main);
    });
    search.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            search.value = '';
            setSearch('');
            search.blur();
        }
    });

    document.addEventListener('keydown', (e) => {
        const typing = /^(INPUT|TEXTAREA)$/.test(document.activeElement.tagName);
        const modalOpen = document.getElementById('project-modal').classList.contains('active');
        if (e.key === '/' && !typing && !modalOpen) {
            e.preventDefault();
            search.focus();
        }
    });

    const links = [...document.querySelectorAll('.nav-sections a')];
    links.forEach(link => link.addEventListener('click', (e) => {
        e.preventDefault();
        const section = document.querySelector(`.project-section[data-section="${link.dataset.section}"], .showcase[data-section="${link.dataset.section}"]`);
        if (!section) return;
        if (section.hidden) clearFilters({ alsoSearch: true });
        if (link.dataset.section === 'all' || link.dataset.section === 'featured') {
            // Land where the page snaps to: the carousel, or the list heading with the filter bar under it.
            scrollBelowNav(link.dataset.section === 'all' ? document.getElementById('list-heading') : section);
        } else {
            scrollToSection(section);
        }
    }));

    const observer = new IntersectionObserver(entries => {
        entries.filter(entry => entry.isIntersecting).forEach(entry => {
            links.forEach(link => link.classList.toggle('active', link.dataset.section === entry.target.dataset.section));
        });
    }, { rootMargin: '-30% 0px -60% 0px' });
    document.querySelectorAll('.project-section, .showcase').forEach(section => observer.observe(section));
}

let modalTocTargets = [];

function renderModalToc() {
    const toc = document.getElementById('modal-toc');
    modalTocTargets = [document.getElementById('modal-description'), ...document.querySelectorAll('#modal-body-container[data-toc], #modal-body-container [data-toc]')];
    toc.innerHTML = '';
    toc.hidden = modalTocTargets.length < 2;
    modalTocTargets.forEach(target => {
        const link = createElement('button', 'modal-toc-link', target.dataset.toc);
        link.type = 'button';
        link.addEventListener('click', () => scrollModalTo(target));
        toc.appendChild(link);
    });
    updateModalToc();
}

// Where content ends up hidden under the sticky section bar.
function modalStickyBottom(scroller) {
    const toc = document.getElementById('modal-toc');
    const pad = parseFloat(getComputedStyle(scroller).paddingTop);
    return scroller.getBoundingClientRect().top + pad + (toc.hidden ? 0 : toc.offsetHeight);
}

function scrollModalTo(target) {
    const scroller = document.querySelector('.modal-scroll');
    const top = target === modalTocTargets[0] ? 0
        : scroller.scrollTop + target.getBoundingClientRect().top - modalStickyBottom(scroller) - 8;
    scroller.scrollTo({ top, behavior: 'smooth' });
}

function updateModalToc() {
    const toc = document.getElementById('modal-toc');
    if (toc.hidden) return;
    const scroller = document.querySelector('.modal-scroll');
    const line = modalStickyBottom(scroller) + 16;
    const atEnd = scroller.scrollTop > 0 && scroller.scrollTop + scroller.clientHeight >= scroller.scrollHeight - 2;
    let current = 0;
    modalTocTargets.forEach((target, i) => {
        if (target.getBoundingClientRect().top <= line) current = i;
    });
    if (atEnd) current = modalTocTargets.length - 1;
    [...toc.children].forEach((link, i) => link.setAttribute('aria-current', String(i === current)));
}

function updateScrollHint() {
    const scroller = document.querySelector('.modal-scroll');
    const hint = document.getElementById('modal-scroll-hint');
    hint.hidden = scroller.scrollTop > 40 || scroller.scrollHeight - scroller.clientHeight < 40;
}

function initScrollHint() {
    const scroller = document.querySelector('.modal-scroll');
    const hint = document.getElementById('modal-scroll-hint');
    hint.querySelector('button').addEventListener('click', () => {
        scroller.scrollBy({ top: scroller.clientHeight * 0.7, behavior: 'smooth' });
    });
    scroller.addEventListener('scroll', updateScrollHint, { passive: true });
    scroller.addEventListener('scroll', updateModalToc, { passive: true });
    new ResizeObserver(updateScrollHint).observe(document.getElementById('modal-body-container'));
}

// The nav's Skills drop-down holds a second copy of the header's skills, for picking skills from anywhere on the
// page. It stays open while skills are picked, so several can be combined.
function initFilterToggle() {
    const panel = document.getElementById('nav-skills-panel');
    const toggle = document.getElementById('nav-skills-toggle');
    const setOpen = (open) => {
        panel.hidden = !open;
        toggle.setAttribute('aria-expanded', open);
    };
    toggle.addEventListener('click', () => setOpen(panel.hidden));
    document.addEventListener('pointerdown', (e) => {
        if (!panel.hidden && !panel.contains(e.target) && !toggle.contains(e.target)) setOpen(false);
    });
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && !panel.hidden) {
            setOpen(false);
            toggle.focus();
        }
    });
}

const VIEW_KEY = 'portfolio.view';

function setView(view) {
    document.body.classList.toggle('view-list', view === 'list');
    fitTagRows();
    document.querySelectorAll('.view-toggle button').forEach(button => {
        button.setAttribute('aria-pressed', button.dataset.view === view);
    });
    try { localStorage.setItem(VIEW_KEY, view); } catch {}
}

function initViewToggle() {
    let view = 'cards';
    try { view = localStorage.getItem(VIEW_KEY) || 'cards'; } catch {}
    setView(view);
    document.querySelectorAll('.view-toggle button').forEach(button => {
        button.addEventListener('click', () => setView(button.dataset.view));
    });
}

function initSearchInvite() {
    const nav = document.querySelector('.nav-search');
    const search = document.getElementById('search');
    nav.classList.add('inviting');
    search.addEventListener('focus', () => nav.classList.remove('inviting'), { once: true });
}

window.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('project-modal');
    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
    });
    modal.querySelector('.modal-close').addEventListener('click', closeModal);
    modal.querySelectorAll('.modal-nav').forEach(button => {
        button.addEventListener('click', () => stepModal(Number(button.dataset.step), button));
    });
    document.addEventListener('keydown', (e) => {
        if (!modal.classList.contains('active')) return;
        if (e.key === 'Escape') closeModal();
        else if ((e.key === 'ArrowLeft' || e.key === 'ArrowRight') && !e.defaultPrevented && !e.altKey && !e.ctrlKey && !e.metaKey && !e.shiftKey
            && !document.activeElement.closest('input, textarea, video, [role="tablist"]')) {
            e.preventDefault();
            stepModal(e.key === 'ArrowRight' ? 1 : -1, document.activeElement.closest('.modal-nav'));
        } else trapFocus(e, modal);
    });
    window.addEventListener('hashchange', syncModalToHash);
    initNav();
    initScrollHint();
    initSearchInvite();
    initViewToggle();
    initFilterToggle();
    trackStickyHeights();
    document.getElementById('clear-filters').addEventListener('click', () => clearFilters({ alsoSearch: true }));
    document.getElementById('no-results-clear').addEventListener('click', () => clearFilters({ alsoSearch: true }));

    loadProjects()
        .then(loaded => {
            projects = loaded;
            projects.forEach(p => p.searchWords = buildSearchWords(p));
            searchVocabulary = [...new Set(projects.flatMap(p => p.searchWords))];
            renderTagFilters();
            renderProjects();
            renderShowcase();
            fitShowcase();
            document.fonts?.ready.then(fitShowcase);
            let fitFrame = 0;
            window.addEventListener('resize', () => {
                cancelAnimationFrame(fitFrame);
                fitFrame = requestAnimationFrame(() => {
                    fitShowcase();
                    fitTagRows();
                });
            });
            applyFilter();
            if (location.hash) syncModalToHash();
        })
        .catch(err => {
            document.querySelector('.showcase-track').textContent =
                'Error loading projects: ' + err.message;
        });
});

// The function-level layer of the codebase map (installed by the codebase-map skill): every function, component,
// class, config object and type in the project's code, with its arguments, what it returns, what it calls, the
// decisions it makes and what it touches outside the app (database, files, email, network).
//   TypeScript/JavaScript: read with the TypeScript compiler the project already installs, so types are the real ones.
//   Python: read by code_py.py with Python's own parser (standard library only, Python 3.8+), same output shape.
// Called by scan.mjs; writes nothing.
import { execFileSync } from 'node:child_process'
import { existsSync } from 'node:fs'
import { createRequire } from 'node:module'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const MAX_STEPS = 400
const SRC = /\.(ts|tsx|mts|cts|js|jsx|mjs|cjs)$/
// Folders and files that are built, vendored, generated or plain config: never mapped. The map's own folder
// (scanner, viewer, data.js, content.mjs) is skipped too, or its .js files would look like a JavaScript project.
const SKIP =
	/(^|\/)(node_modules|dist|build|out|\.next|\.nuxt|\.svelte-kit|\.turbo|\.vercel|\.output|coverage|public|static|vendor|migrations?|__generated__|generated)\/|\.d\.[cm]?ts$|\.min\.js$|(^|\/)[^/]*\.config\.[cm]?[jt]s$|(^|\/)\.[^/]*rc\.[cm]?js$|(^|\/)codebase-map\//
const TEST = /(^|\/)(__tests__|tests?|e2e|spec|cypress|playwright)\/|\.(test|spec)\.[cm]?[jt]sx?$/
const HTTP = new Set(['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS', 'HEAD'])
const ROUTE_LIBS = /^(express|fastify|hono|koa|@koa\/router|koa-router|h3|elysia|restify|polka|@hono\/.+)$/
const matches = (file, rule) =>
	rule.startsWith('/') && rule.endsWith('/') ? new RegExp(rule.slice(1, -1)).test(file) : file.startsWith(rule)
const under = (file, root) => !root || file.startsWith(`${root}/`)

/** The projects to read: the config's list, else one per tsconfig/jsconfig, else the whole repo. */
export function codeProjects(paths, configured) {
	if (configured?.length) return configured.map((p) => ({ name: p.name ?? (p.root || 'root'), root: p.root ?? '', ...p }))
	const configs = paths.filter((f) => /(^|\/)(tsconfig|jsconfig)\.json$/.test(f) && !SKIP.test(f))
	const roots = [...new Set(configs.map((f) => (path.posix.dirname(f) === '.' ? '' : path.posix.dirname(f))))]
	if (!roots.includes('') && paths.some((f) => SRC.test(f) && !SKIP.test(f) && !roots.some((r) => under(f, r)))) roots.push('')
	return roots.sort().map((root) => {
		const tsconfig = configs.find((f) => f === (root ? `${root}/tsconfig.json` : 'tsconfig.json')) ?? configs.find((f) => f === (root ? `${root}/jsconfig.json` : 'jsconfig.json'))
		return { name: root || 'root', root, ...(tsconfig ? { tsconfig } : {}) }
	})
}

/**
 * Every language the map can read, merged into one result for code.js.
 * opts: { python: { enabled, interpreter, include, exclude, paths }, envReaders: [] } from map.config.mjs.
 * Python's import graph comes back as `imports` (for the Code tab), to be taken out before code.js is written.
 */
export function scanCode(ROOT, paths, warnings, configured = [], packages = { list: [], manager: 'npm' }, generated = new Set(), opts = {}) {
	const ts = scanTs(ROOT, paths, warnings, configured, packages, generated)
	const py = opts.python?.enabled === false ? null : scanPython(ROOT, paths, warnings, opts, generated)
	const missing = [ts.missing, py?.missing].filter(Boolean)
	const out = {
		projects: [...ts.projects.map((p) => ({ ...p, lang: 'ts' })), ...(py?.symbols.length ? [{ name: 'Python', root: '', lang: 'python' }] : [])],
		symbols: [...ts.symbols, ...(py?.symbols ?? [])],
		entries: [...ts.entries, ...(py?.entries ?? [])].sort((a, b) => a.kind.localeCompare(b.kind) || a.trigger.localeCompare(b.trigger)),
		wiring: [...ts.wiring, ...(py?.wiring ?? [])],
		tests: { ...ts.tests },
		sources: { ...ts.sources, ...(py?.sources ?? {}) },
		imports: py?.imports ?? {},
	}
	for (const [id, list] of Object.entries(py?.tests ?? {})) out.tests[id] = [...(out.tests[id] ?? []), ...list]
	if (missing.length) out.missing = missing
	return out
}

/** A Python 3.8+ to run code_py.py: the config's, CODEMAP_PYTHON, the repo's virtualenv, then the PATH's. */
function findPython(ROOT, configured) {
	const venvs = ['.venv', 'venv', 'env', '.env'].flatMap((d) => [path.join(ROOT, d, 'Scripts', 'python.exe'), path.join(ROOT, d, 'bin', 'python')])
	const candidates = [
		...[configured, process.env.CODEMAP_PYTHON].filter(Boolean).map((p) => [path.isAbsolute(p) ? p : path.join(ROOT, p), []]),
		...venvs.filter((p) => existsSync(p)).map((p) => [p, []]),
		['python3', []],
		['python', []],
		['py', ['-3']],
	]
	for (const [exe, pre] of candidates) {
		try {
			const ok = execFileSync(exe, [...pre, '-c', 'import sys; print(sys.version_info >= (3, 8))'], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'], timeout: 20000 }).trim()
			if (ok === 'True') return [exe, pre]
		} catch {}
	}
	return null
}

function scanPython(ROOT, paths, warnings, opts, generated) {
	const files = paths.filter((f) => f.endsWith('.py') && !SKIP.test(f))
	if (!files.length) return null
	const cfg = opts.python ?? {}
	const py = findPython(ROOT, cfg.interpreter)
	if (!py) {
		warnings.push('code map: no Python 3.8+ found (set python.interpreter in map.config.mjs, or CODEMAP_PYTHON). The Python functions are left out.')
		return { symbols: [], entries: [], wiring: [], tests: {}, sources: {}, imports: {}, missing: 'python' }
	}
	const script = path.join(path.dirname(fileURLToPath(import.meta.url)), 'code_py.py')
	const request = { root: ROOT, files, config: cfg, envReaders: opts.envReaders ?? [], generated: [...generated] }
	let res
	try {
		// -I: isolated mode, so nothing in the repo or the environment is imported alongside the scanner.
		const out = execFileSync(py[0], [...py[1], '-I', script], { input: JSON.stringify(request), encoding: 'utf8', maxBuffer: 1024 * 1024 * 1024, stdio: ['pipe', 'pipe', 'pipe'] })
		res = JSON.parse(out)
	} catch (e) {
		warnings.push(`code map: the Python scanner failed (${String(e.stderr || e.message).trim().split('\n').at(-1)}). The Python functions are left out.`)
		return { symbols: [], entries: [], wiring: [], tests: {}, sources: {}, imports: {}, missing: 'python' }
	}
	warnings.push(...(res.warnings ?? []))
	return res
}

function scanTs(ROOT, paths, warnings, configured = [], packages = { list: [], manager: 'npm' }, generated = new Set()) {
	const projects = codeProjects(paths, configured)
	const empty = { projects: [], symbols: [], entries: [], wiring: [], tests: {}, sources: {} }
	if (!projects.length) return empty
	// The project's own TypeScript, so types match its version. CODEMAP_TYPESCRIPT may point at one elsewhere.
	let ts = null
	for (const from of [...projects.map((p) => path.join(ROOT, p.root, 'package.json')), path.join(ROOT, 'package.json'), process.env.CODEMAP_TYPESCRIPT && path.join(process.env.CODEMAP_TYPESCRIPT, 'x.js')].filter(Boolean)) {
		try {
			ts = createRequire(from)('typescript')
			break
		} catch {}
	}
	if (!ts) {
		warnings.push('code map: TypeScript not found (install it as a dev dependency, or set CODEMAP_TYPESCRIPT to a folder that has it). The Functions tab is empty.')
		return { ...empty, missing: 'typescript' }
	}
	const K = ts.SyntaxKind
	const rel = (abs) => path.relative(ROOT, abs).split(path.sep).join('/')
	const hasNext = packages.list.some((p) => p.dependencies?.next || p.devDependencies?.next)
	// Each file belongs to the innermost project that contains it.
	const owner = (f) => [...projects].sort((a, b) => b.root.length - a.root.length).find((p) => under(f, p.root))
	const inScope = (f, p) =>
		SRC.test(f) && !SKIP.test(f) && !TEST.test(f) && !generated.has(f) && owner(f) === p &&
		(!p.include?.length || p.include.some((r) => matches(f, r))) && !(p.exclude ?? []).some((r) => matches(f, r))
	const scopeFiles = new Map(projects.map((p) => [p, paths.filter((f) => inScope(f, p))]))
	const scope = new Set([...scopeFiles.values()].flat())
	const testFiles = paths.filter((f) => SRC.test(f) && TEST.test(f) && !/(^|\/)node_modules\//.test(f) && owner(f))
	const pkgScripts = packages.list.flatMap((pk) => [...Object.entries(pk.scripts ?? {}), ...Object.entries(pk.bin ?? {}).map(([n, b]) => [n, `bin ${b}`])].map(([name, cmd]) => ({ pk, name, cmd })))
	const scriptFor = (file) =>
		pkgScripts.find(({ pk, cmd }) => {
			const relToPkg = pk.dir ? (file.startsWith(`${pk.dir}/`) ? file.slice(pk.dir.length + 1) : null) : file
			return relToPkg && new RegExp(`(^|[\\s/.'"])${relToPkg.replace(/[.*+?^${}()|[\]\\]/g, '\\$&').replace(/\\\.[cm]?[jt]sx?$/, '')}(\\.[cm]?[jt]sx?)?(\\s|$|['"])`).test(cmd)
		})
	const isScriptFile = (file) => Boolean(scriptFor(file)) || /(^|\/)(scripts?|bin|cli)\//.test(file)
	const runCmd = (pk, name) =>
		packages.manager === 'pnpm'
			? pk.dir ? `pnpm --filter ${pk.name} ${name}` : `pnpm ${name}`
			: packages.manager === 'yarn'
				? pk.dir ? `yarn workspace ${pk.name} ${name}` : `yarn ${name}`
				: packages.manager === 'bun'
					? `bun run ${name}`
					: pk.dir ? `npm run ${name} -w ${pk.dir}` : `npm run ${name}`

	const DEFAULT_OPTIONS = {
		allowJs: true,
		checkJs: false,
		jsx: ts.JsxEmit.Preserve,
		module: ts.ModuleKind.ESNext,
		moduleResolution: ts.ModuleResolutionKind.Bundler ?? ts.ModuleResolutionKind.NodeJs,
		target: ts.ScriptTarget.ES2022,
		resolveJsonModule: true,
		esModuleInterop: true,
		skipLibCheck: true,
	}
	const sourceOf = new Map()
	const checkerOf = new Map()
	for (const p of projects) {
		const files = [...scopeFiles.get(p), ...testFiles.filter((f) => owner(f) === p)]
		if (!files.length) continue
		let options = DEFAULT_OPTIONS
		if (p.tsconfig && existsSync(path.join(ROOT, p.tsconfig))) {
			const cfg = ts.readConfigFile(path.join(ROOT, p.tsconfig), ts.sys.readFile)
			const parsed = ts.parseJsonConfigFileContent(cfg.config ?? {}, ts.sys, path.dirname(path.join(ROOT, p.tsconfig)))
			options = { ...parsed.options, allowJs: true }
		}
		const program = ts.createProgram(
			files.map((f) => path.join(ROOT, f)),
			{ ...options, incremental: false, composite: false, noEmit: true, tsBuildInfoFile: undefined },
		)
		const checker = program.getTypeChecker()
		for (const sf of program.getSourceFiles()) {
			const f = rel(sf.fileName)
			if (files.includes(f) && !sourceOf.has(f)) {
				sourceOf.set(f, sf)
				checkerOf.set(f, checker)
			}
		}
	}
	let checker = null

	// ------------------------------------------------------------ text helpers
	let sf = null
	const squash = (s) => s.replace(/\s+/g, ' ').trim()
	const cut = (s, n) => (s.length > n ? `${s.slice(0, n - 1)}…` : s)
	const short = (node, n = 90) => (node ? cut(squash(node.getText(sf)), n) : '')
	const lineOf = (pos) => sf.getLineAndCharacterOfPosition(pos).line + 1
	const typeStr = (t) =>
		cut(
			squash(
				checker.typeToString(t, undefined, ts.TypeFormatFlags.UseAliasDefinedOutsideCurrentScope),
			).replace(/import\("[^"]*"\)\./g, ''),
			200,
		)
	const isFn = (n) =>
		n && (n.kind === K.ArrowFunction || n.kind === K.FunctionExpression || n.kind === K.FunctionDeclaration)
	const unwrap = (n) => {
		while (
			n &&
			(n.kind === K.ParenthesizedExpression ||
				n.kind === K.AsExpression ||
				n.kind === K.SatisfiesExpression ||
				n.kind === K.NonNullExpression ||
				n.kind === K.TypeAssertionExpression)
		)
			n = n.expression
		return n
	}
	const hasMod = (n, kind) => Boolean(n.modifiers?.some((m) => m.kind === kind))
	const nameText = (n) =>
		n && (ts.isIdentifier(n) || ts.isStringLiteral(n)) ? n.text : n ? short(n, 40) : ''

	/** The comment written directly above a declaration (`/** … *\/` or `//` lines), without markers or tags. */
	function docOf(node) {
		const text = sf.text
		const ranges = ts.getLeadingCommentRanges(text, node.getFullStart()) ?? []
		const kept = []
		let end = node.getStart(sf)
		for (const r of [...ranges].reverse()) {
			if (/\n\s*\n/.test(text.slice(r.end, end))) break
			kept.unshift(text.slice(r.pos, r.end))
			end = r.pos
		}
		const params = {}
		const lines = []
		for (const c of kept) {
			const body = c.startsWith('/*')
				? c
						.replace(/^\/\*\*?/, '')
						.replace(/\*\/$/, '')
						.split('\n')
						.map((l) => l.replace(/^\s*\* ?/, ''))
				: [c.replace(/^\/\/\s?/, '')]
			for (const l of body) {
				const p = l.match(/^@param\s+(?:\{[^}]*\}\s*)?(\w+)\s*-?\s*(.*)$/)
				if (p) params[p[1]] = p[2]
				else if (!/^@\w+/.test(l.trim())) lines.push(l.trim())
			}
		}
		const doc = lines
			.join('\n')
			.replace(/\n{2,}/g, '\n\n')
			.replace(/([^\n])\n(?![\n-])/g, '$1 ')
			.trim()
		return { doc, params }
	}

	// ------------------------------------------------------------ pass 1: declarations
	const symbols = []
	const byId = new Map()
	const routeRegs = []
	const byDecl = new Map() // declaration node → symbol
	const byFn = new Map() // function node → symbol
	const sources = {}

	function routeUrl(file) {
		const pages = file.match(/(?:^|\/)pages\/(.+?)\.[cm]?[jt]sx?$/)
		const m = pages ? null : file.match(/(?:^|\/)app\/(.*?)([^/]+)$/)
		if (!m && !pages) return null
		const url = (pages ? pages[1].replace(/(^|\/)index$/, '') : m[1])
			.split('/')
			.filter(Boolean)
			.filter((s) => !/^\(.+\)$/.test(s) && !s.startsWith('@'))
			.map((s) =>
				s
					.replace(/^\[\[\.\.\..+\]\]$/, '*')
					.replace(/^\[\.\.\..+\]$/, '*')
					.replace(/^\[(.+)\]$/, ':$1'),
			)
			.join('/')
		return `/${url}`
	}

	function add(sym, declNode, fnNode) {
		sym.line = lineOf(declNode.getStart(sf))
		sym.end = lineOf(declNode.getEnd())
		symbols.push(sym)
		sym._decl = declNode
		sym._fn = fnNode ?? null
		sym._sf = sf
		byId.set(sym.id, sym)
		byDecl.set(declNode, sym)
		if (fnNode) byFn.set(fnNode, sym)
		return sym
	}

	/** A variable's function, looking through wrappers such as `cache(async () => …)`. */
	function fnOfInit(init) {
		const u = unwrap(init)
		if (isFn(u)) return { fn: u }
		if (u?.kind === K.CallExpression) {
			const f = u.arguments.find((a) => isFn(unwrap(a)))
			if (f) return { fn: unwrap(f), wrapper: short(u.expression, 40) }
		}
		return null
	}

	function kindFor(sym, file, fn, typeText, init) {
		const baseName = path.posix.basename(file).replace(/\.[cm]?[jt]sx?$/, '')
		const inPages = hasNext && /(^|\/)pages\//.test(file) && !/(^|\/)app\//.test(file)
		const inApp = hasNext && !inPages && /(^|\/)app\//.test(file)
		if (inApp && sym.isDefault && /^(page|not-found|error|global-error)$/.test(baseName)) return 'page'
		if (inApp && sym.isDefault && /^(layout|template)$/.test(baseName)) return 'layout'
		if (inApp && sym.isDefault && /^(robots|sitemap|manifest)$/.test(baseName)) return 'endpoint'
		if (inApp && baseName === 'route' && sym.exported && HTTP.has(sym.name)) return 'endpoint'
		if (inApp && sym.exported && /^(generateMetadata|generateStaticParams)$/.test(sym.name)) return 'meta'
		if (inPages && sym.isDefault && !/(^|\/)_(app|document|error)\.[cm]?[jt]sx?$/.test(file)) return /(^|\/)pages\/api\//.test(file) ? 'endpoint' : 'page'
		if (inPages && sym.exported && /^(getServerSideProps|getStaticProps|getStaticPaths)$/.test(sym.name)) return 'meta'
		if (/(^|\/)(src\/)?(middleware|proxy)\.[cm]?[jt]s$/.test(file) && (sym.isDefault || /^(middleware|proxy)$/.test(sym.name))) return 'proxy'
		if (/(^|\/)(src\/)?instrumentation\.[cm]?[jt]s$/.test(file) && sym.name === 'register') return 'startup'
		if (sym.directive === 'use server' && sym.exported && fn) return 'action'
		if (typeText) {
			if (/\bTaskConfig\b/.test(typeText)) return 'task'
			if (/\bCollectionConfig\b/.test(typeText)) return 'collection'
			if (/\bGlobalConfig\b/.test(typeText)) return 'global'
			if (/Hook\b/.test(typeText)) return 'hook'
			if (/^(Access|FieldAccess)\b/.test(typeText)) return 'access'
			if (/\bValidate\b/.test(typeText)) return 'validate'
			if (/Field\b/.test(typeText) && !fn) return 'field'
		}
		if (fn) {
			const jsx = (() => {
				let found = false
				const v = (n) => {
					if (found) return
					if (n.kind === K.JsxElement || n.kind === K.JsxSelfClosingElement || n.kind === K.JsxFragment)
						found = true
					else ts.forEachChild(n, v)
				}
				v(fn)
				return found
			})()
			if (/^[A-Z]/.test(sym.name) && jsx) return 'component'
			return 'function'
		}
		if (init && unwrap(init).kind === K.ObjectLiteralExpression) return 'object'
		return 'value'
	}

	function collectInner(parent, fnNode) {
		const visit = (n) => {
			if (n.kind === K.FunctionDeclaration && n.name && n !== fnNode) {
				const s = add(
					{
						id: `${parent.id}.${n.name.text}`,
						name: n.name.text,
						file: parent.file,
						kind: 'function',
						parent: parent.id,
						async: hasMod(n, K.AsyncKeyword),
						...docOf(n),
					},
					n,
					n,
				)
				collectInner(s, n)
				return
			}
			if (n.kind === K.VariableDeclaration && ts.isIdentifier(n.name) && n.initializer) {
				const f = fnOfInit(n.initializer)
				if (f) {
					const stmt = n.parent?.parent
					const s = add(
						{
							id: `${parent.id}.${n.name.text}`,
							name: n.name.text,
							file: parent.file,
							kind: 'function',
							parent: parent.id,
							async: hasMod(f.fn, K.AsyncKeyword),
							...(f.wrapper ? { wrapper: f.wrapper } : {}),
							...docOf(stmt?.kind === K.VariableStatement ? stmt : n),
						},
						n,
						f.fn,
					)
					collectInner(s, f.fn)
					return
				}
			}
			ts.forEachChild(n, visit)
		}
		if (fnNode.body) ts.forEachChild(fnNode.body, visit)
	}

	for (const file of [...scope].sort()) {
		sf = sourceOf.get(file)
		checker = checkerOf.get(file)
		if (!sf) {
			warnings.push(`code map: TypeScript didn't load ${file}`)
			continue
		}
		sources[file] = sf.text
		const first = sf.statements[0]
		const directive =
			first?.kind === K.ExpressionStatement && ts.isStringLiteral(first.expression)
				? first.expression.text
				: null
		const exportedNames = new Set()
		let defaultName = null
		for (const st of sf.statements) {
			if (st.kind === K.ExportDeclaration && !st.moduleSpecifier && st.exportClause?.elements)
				for (const e of st.exportClause.elements) exportedNames.add((e.propertyName ?? e.name).text)
			if (st.kind === K.ExportAssignment && ts.isIdentifier(st.expression)) defaultName = st.expression.text
		}
		const base = { file, ...(directive ? { directive } : {}) }
		const topLevel = []

		for (const st of sf.statements) {
			const exported = hasMod(st, K.ExportKeyword)
			const isDefault = hasMod(st, K.DefaultKeyword)
			if (st.kind === K.FunctionDeclaration) {
				const name = st.name?.text ?? 'default'
				const sym = {
					...base,
					id: `${file}#${name}`,
					name,
					exported: exported || exportedNames.has(name) || defaultName === name,
					isDefault: isDefault || defaultName === name,
					async: hasMod(st, K.AsyncKeyword),
					...docOf(st),
				}
				sym.kind = kindFor(sym, file, st)
				add(sym, st, st)
				collectInner(sym, st)
			} else if (
				st.kind === K.VariableStatement &&
				isScriptFile(file) &&
				st.declarationList.declarations.every((d) => !d.initializer || !fnOfInit(d.initializer))
			) {
				topLevel.push(st)
			} else if (st.kind === K.VariableStatement) {
				for (const d of st.declarationList.declarations) {
					// `export const { GET, POST } = toNextJsHandler(…)`: one symbol per name, sharing the value.
					if (d.name.kind === K.ObjectBindingPattern) {
						for (const el of d.name.elements) {
							if (!ts.isIdentifier(el.name)) continue
							const sym = {
								...base,
								id: `${file}#${el.name.text}`,
								name: el.name.text,
								exported: exported || exportedNames.has(el.name.text),
								...docOf(st),
							}
							sym.kind = kindFor(sym, file, null, '', d.initializer)
							add(sym, el, null)._init = d.initializer
						}
						continue
					}
					if (!ts.isIdentifier(d.name)) continue
					const name = d.name.text
					const f = d.initializer && fnOfInit(d.initializer)
					const typeText = d.type ? d.type.getText(sf) : ''
					const sym = {
						...base,
						id: `${file}#${name}`,
						name,
						exported: exported || exportedNames.has(name) || defaultName === name,
						isDefault: defaultName === name,
						...(f ? { async: hasMod(f.fn, K.AsyncKeyword) } : {}),
						...(f?.wrapper ? { wrapper: f.wrapper } : {}),
						...(typeText ? { declared: cut(squash(typeText), 120) } : {}),
						...docOf(st),
					}
					sym.kind = kindFor(sym, file, f?.fn, typeText, d.initializer)
					add(sym, d, f?.fn)
					if (f) collectInner(sym, f.fn)
				}
			} else if (st.kind === K.ClassDeclaration) {
				const name = st.name?.text ?? 'default'
				const cls = add(
					{
						...base,
						id: `${file}#${name}`,
						name,
						kind: 'class',
						exported: exported || exportedNames.has(name),
						isDefault,
						...(st.heritageClauses ? { extends: short(st.heritageClauses[0], 60) } : {}),
						...docOf(st),
					},
					st,
					null,
				)
				for (const m of st.members) {
					const mName =
						m.kind === K.Constructor ? 'constructor' : m.name && ts.isIdentifier(m.name) ? m.name.text : null
					if (!mName) continue
					const fn =
						m.kind === K.MethodDeclaration || m.kind === K.Constructor
							? m
							: m.kind === K.PropertyDeclaration && isFn(unwrap(m.initializer))
								? unwrap(m.initializer)
								: null
					if (!fn) continue
					add(
						{
							...base,
							id: `${cls.id}.${mName}`,
							name: mName,
							kind: 'method',
							parent: cls.id,
							async: hasMod(fn, K.AsyncKeyword),
							...docOf(m),
						},
						m,
						fn,
					)
				}
			} else if (
				st.kind === K.InterfaceDeclaration ||
				st.kind === K.TypeAliasDeclaration ||
				st.kind === K.EnumDeclaration
			) {
				const name = st.name.text
				add(
					{
						...base,
						id: `${file}#${name}`,
						name,
						kind: 'type',
						exported: exported || exportedNames.has(name),
						...docOf(st),
					},
					st,
					null,
				)
			} else if (st.kind === K.ExportAssignment && !ts.isIdentifier(st.expression)) {
				const sym = {
					...base,
					id: `${file}#default`,
					name: 'default',
					exported: true,
					isDefault: true,
					...docOf(st),
				}
				const f = fnOfInit(st.expression)
				sym.kind = f ? kindFor(sym, file, f.fn) : 'object'
				add(sym, st, f?.fn)
			} else if (
				st.kind !== K.ImportDeclaration &&
				st.kind !== K.ExportDeclaration &&
				st.kind !== K.ExportAssignment &&
				st.kind !== K.ModuleDeclaration &&
				!(st === first && directive)
			) {
				topLevel.push(st)
			}
		}
		// A script's own statements run top to bottom when it's started.
		if (topLevel.length) {
			const sym = {
				...base,
				id: `${file}#(top level)`,
				name: '(top level)',
				kind: isScriptFile(file) ? 'script' : 'module',
				exported: false,
				doc: docOf(topLevel[0]).doc,
				params: {},
			}
			sym.line = lineOf(topLevel[0].getStart(sf))
			sym.end = lineOf(topLevel.at(-1).getEnd())
			sym._top = topLevel
			sym._sf = sf
			symbols.push(sym)
		}
	}

	// ------------------------------------------------------------ resolving names
	const pkgOf = (fileName) => {
		const f = fileName.replace(/\\/g, '/')
		if (/\/typescript\/lib\/lib\.[^/]*\.d\.ts$/.test(f)) return 'js'
		const i = f.lastIndexOf('/node_modules/')
		if (i < 0) return 'js'
		const parts = f.slice(i + 14).split('/')
		let name = parts[0].startsWith('@') ? `${parts[0]}/${parts[1]}` : parts[0]
		if (name.startsWith('@types/')) name = name.slice(7)
		if (name === 'undici-types') name = 'node'
		return name
	}

	/** What a name refers to: one of our symbols, a parameter, or something from a library. */
	function resolve(expr) {
		const at = expr.kind === K.PropertyAccessExpression ? expr.name : expr
		let s
		try {
			s = checker.getSymbolAtLocation(at)
			if (s && s.flags & ts.SymbolFlags.Alias) s = checker.getAliasedSymbol(s)
		} catch {
			return null
		}
		const d = s?.valueDeclaration ?? s?.declarations?.[0]
		if (!d) return null
		const file = rel(d.getSourceFile().fileName)
		if (scope.has(file)) {
			if (byDecl.has(d)) return { sym: byDecl.get(d) }
			// Declared in another project (a shared package): the same top-level name, found by id.
			const declName = d.name && ts.isIdentifier(d.name) ? d.name.text : null
			const other = declName && byId.get(`${file}#${declName}`)
			if (other && other._sf !== sf) return { sym: other }
			if (d.kind === K.Parameter) return { param: s.name }
			if (d.kind === K.BindingElement) {
				let n = d.parent
				while (
					n &&
					(n.kind === K.ObjectBindingPattern ||
						n.kind === K.ArrayBindingPattern ||
						n.kind === K.BindingElement)
				)
					n = n.parent
				if (n?.kind === K.Parameter) return { param: s.name }
			}
			// A method of an object made inside one of our functions (`limiter.take`): credit the maker.
			if (
				d.kind === K.MethodDeclaration ||
				d.kind === K.PropertyAssignment ||
				d.kind === K.ShorthandPropertyAssignment
			)
				for (let n = d.parent; n; n = n.parent) if (byDecl.has(n)) return { sym: byDecl.get(n), via: s.name }
			return { local: s.name }
		}
		return { ext: true, pkg: pkgOf(d.getSourceFile().fileName), name: s.name }
	}

	const DB_READ = /^(find|findByID|count|findGlobal|findVersions|findDistinct|findOne)$/
	const DB_WRITE = /^(create|update|delete|updateGlobal|duplicate|restoreVersion|upsert)$/
	/** What a library call does, in one word; null for plain JavaScript helpers that aren't worth a step. */
	function effectOf(pkg, name, owner) {
		if (pkg === 'payload') {
			if (DB_READ.test(name)) return 'db-read'
			if (DB_WRITE.test(name)) return 'db-write'
			if (name === 'sendEmail') return 'email'
			if (name === 'getPayload') return 'setup'
			if (/^(login|logout|forgotPassword|resetPassword|verifyEmail|unlock|auth)$/.test(name)) return 'auth'
			if (/^(queue|run|runByID)$/.test(name)) return 'job'
			if (/^(info|error|warn|debug)$/.test(name)) return 'log'
			return 'payload'
		}
		if (pkg === '@payloadcms/db-postgres' || pkg === 'drizzle-orm' || pkg === 'pg')
			return /^(execute|query)$/.test(name) ? 'db-raw' : 'payload'
		if (pkg === 'next') {
			if (/^(redirect|permanentRedirect)$/.test(name)) return 'redirect'
			if (/^(notFound|forbidden|unauthorized)$/.test(name)) return 'notfound'
			if (/^(cookies|headers|draftMode)$/.test(name)) return 'request'
			if (/^(revalidatePath|revalidateTag|updateTag|unstable_cache|cacheTag|cacheLife)$/.test(name))
				return 'cache'
			if (/^(next|rewrite|json)$/.test(name)) return 'response'
			if (/^(useRouter|usePathname|useSearchParams|useParams)$/.test(name)) return 'ui'
			return 'next'
		}
		if (pkg === 'react' || pkg === 'react-dom')
			return /^use[A-Z]/.test(name) ? 'ui' : name === 'cache' ? 'cache' : null
		if (pkg === 'zod') return /^(parse|safeParse|parseAsync|safeParseAsync)$/.test(name) ? 'validate' : null
		if (pkg === 'nodemailer') return /^(sendMail)$/.test(name) ? 'email' : null
		if (pkg === 'meilisearch') return 'search'
		if (pkg.startsWith('@aws-sdk/')) return /^send$/.test(name) ? 'storage' : null
		if (pkg === 'sharp') return 'image'
		if (pkg === 'better-auth' || pkg.startsWith('@better-auth/')) return 'auth'
		if (pkg === 'node' || pkg === 'js') {
			if (name === 'fetch') return 'network'
			if (owner === 'Response' && /^(json|redirect)$/.test(name)) return 'response'
			if (
				/^(createHmac|createHash|timingSafeEqual|randomBytes|randomUUID|randomInt|digest|update)$/.test(name)
			)
				return pkg === 'node' ? 'crypto' : null
			if (/^(error|warn)$/.test(name)) return 'log'
			if (/^(setTimeout|setInterval)$/.test(name)) return 'timer'
			if (/^(exit)$/.test(name)) return 'exit'
			return null
		}
		if (pkg === 'pino' || pkg === 'winston' || pkg === 'consola') return 'log'
		if (pkg.startsWith('@supabase/')) {
			if (/^(select|maybeSingle|single)$/.test(name)) return 'db-read'
			if (/^(insert|update|upsert|delete)$/.test(name)) return 'db-write'
			if (name === 'rpc') return 'db-raw'
			if (/^(signIn\w*|signUp|signOut|getUser|getSession|exchangeCodeForSession|verifyOtp|resetPasswordForEmail|updateUser)$/.test(name)) return 'auth'
			if (/^(upload|download|remove|list|getPublicUrl|createSignedUrl)$/.test(name)) return 'storage'
			if (/^(createClient|createServerClient|createBrowserClient|createClientComponentClient|createServerComponentClient|createRouteHandlerClient|createMiddlewareClient)$/.test(name)) return 'setup'
			return null
		}
		if (pkg === '@prisma/client' || pkg === '.prisma') {
			if (/^(findMany|findUnique|findUniqueOrThrow|findFirst|findFirstOrThrow|count|aggregate|groupBy)$/.test(name)) return 'db-read'
			if (/^(create|createMany|update|updateMany|upsert|delete|deleteMany)$/.test(name)) return 'db-write'
			if (/^\$(queryRaw|executeRaw|queryRawUnsafe|executeRawUnsafe|transaction)$/.test(name)) return 'db-raw'
			return null
		}
		if (pkg === 'mongoose' || pkg === 'mongodb') {
			if (/^(find|findOne|findById|countDocuments|aggregate|distinct|exists)$/.test(name)) return 'db-read'
			if (/^(create|insertOne|insertMany|updateOne|updateMany|findOneAndUpdate|findByIdAndUpdate|deleteOne|deleteMany|findByIdAndDelete|save|replaceOne|bulkWrite)$/.test(name)) return 'db-write'
			return null
		}
		if (pkg === 'drizzle-orm') return /^(select|query|findMany|findFirst)$/.test(name) ? 'db-read' : /^(insert|update|delete)$/.test(name) ? 'db-write' : /^(execute)$/.test(name) ? 'db-raw' : null
		if (pkg === 'mysql2' || pkg === 'postgres' || pkg === 'better-sqlite3' || pkg === 'sqlite3' || pkg === 'knex' || pkg === 'kysely') return /^(query|execute|run|all|get|raw|exec)$/.test(name) ? 'db-raw' : null
		if (/^(axios|got|ky|node-fetch|undici|superagent|ofetch)$/.test(pkg)) return /^(get|post|put|patch|delete|request|head|fetch|default)$/.test(name) || owner === pkg ? 'network' : null
		if (/^(stripe|razorpay|@paypal\/.+|braintree)$/.test(pkg)) return 'network'
		if (/^(resend|@sendgrid\/mail|postmark|mailgun\.js|@mailchimp\/.+|nodemailer)$/.test(pkg)) return /^(send|sendMail|create|sendEmail)$/.test(name) ? 'email' : null
		if (/^(redis|ioredis|@upstash\/redis|@vercel\/kv)$/.test(pkg)) return 'cache'
		if (/^(jsonwebtoken|jose|bcrypt|bcryptjs|argon2)$/.test(pkg)) return /^(sign|verify|hash|compare|hashSync|compareSync|decode|jwtVerify|SignJWT)$/.test(name) ? 'crypto' : null
		if (/^(next-auth|@auth\/.+|@clerk\/.+|lucia|passport|firebase-admin|@kinde-oss\/.+)$/.test(pkg)) return 'auth'
		if (/^(firebase|@firebase\/.+)$/.test(pkg)) return /^(getDoc|getDocs|query|onSnapshot)$/.test(name) ? 'db-read' : /^(setDoc|addDoc|updateDoc|deleteDoc)$/.test(name) ? 'db-write' : null
		if (/^(react-hot-toast|sonner|lucide-react|clsx|classnames|tailwind-merge|date-fns|dayjs|moment|lodash|uuid|nanoid)$/.test(pkg)) return null
		if (/^(@mui\/.+|@emotion\/.+|framer-motion|gsap|@radix-ui\/.+|@headlessui\/.+)$/.test(pkg)) return /^use[A-Z]/.test(name) ? 'ui' : null
		if (/^@payloadcms\//.test(pkg) || pkg === 'payload-totp') return 'payload'
		return 'lib'
	}

	/** What a database call works on: `payload.find({ collection: 'articles' })`, `supabase.from('bookings').select()`,
	 * `prisma.booking.findMany()` or `Booking.find()`. */
	function dbTarget(call) {
		for (let e = call.expression; e; ) {
			if (e.kind === K.PropertyAccessExpression) e = e.expression
			else if (e.kind === K.CallExpression) {
				const callee = e.expression
				const fn = callee.kind === K.PropertyAccessExpression ? callee.name.text : callee.kind === K.Identifier ? callee.text : ''
				const arg = e.arguments[0] && unwrap(e.arguments[0])
				if (/^(from|table|collection)$/.test(fn) && arg && ts.isStringLiteralLike(arg)) return arg.text
				e = callee
			} else break
		}
		const callee = call.expression
		if (callee.kind === K.PropertyAccessExpression && callee.expression.kind === K.PropertyAccessExpression && /^(prisma|db|client|tx)$/.test(callee.expression.expression.getText(sf)))
			return callee.expression.name.text
		if (callee.kind === K.PropertyAccessExpression && ts.isIdentifier(callee.expression) && /^[A-Z]/.test(callee.expression.text)) return callee.expression.text
		const a = call.arguments[0] && unwrap(call.arguments[0])
		if (a?.kind !== K.ObjectLiteralExpression) return undefined
		for (const p of a.properties) {
			const n = p.name && nameText(p.name)
			if ((n === 'collection' || n === 'slug') && p.kind === K.PropertyAssignment) {
				const v = unwrap(p.initializer)
				return ts.isStringLiteralLike(v) ? v.text : short(v, 30)
			}
		}
		return undefined
	}

	// ------------------------------------------------------------ pass 2: what each function does, in order
	let ctx = null
	const awaited = (n) => {
		let p = n.parent
		while (p && p.kind === K.ParenthesizedExpression) p = p.parent
		return p?.kind === K.AwaitExpression
	}
	const note = (step) => {
		ctx.count++
		return step
	}
	const linkTo = (sym, how) => {
		if (sym === ctx.sym) return
		const prev = ctx.links.get(sym.id)
		if (!prev || (prev !== 'call' && how === 'call')) ctx.links.set(sym.id, how)
	}

	function cbLabel(fn) {
		const p = fn.parent
		if (p?.kind === K.JsxExpression && p.parent?.kind === K.JsxAttribute) return p.parent.name.getText(sf)
		if (p?.kind === K.PropertyAssignment) return nameText(p.name)
		if (p?.kind === K.CallExpression) return `${short(p.expression, 40)}(…)`
		return 'an inline function'
	}

	function body(fn) {
		if (!fn.body) return []
		if (fn.body.kind === K.Block) return stmts(fn.body.statements)
		const steps = expr(fn.body)
		return byFn.has(fn) ? [...steps, retStep(fn.body)] : steps
	}
	const isJsx = (n) => [K.JsxElement, K.JsxSelfClosingElement, K.JsxFragment].includes(unwrap(n)?.kind ?? -1)
	const retStep = (e) =>
		note(e ? (isJsx(e) ? { t: 'ret', jsx: true } : { t: 'ret', v: short(e, 120) }) : { t: 'ret' })

	/** Calls made while working out a condition, listed flat: `a() || b()` is one condition, not two decisions. */
	function condSteps(n) {
		const was = ctx.cond
		ctx.cond = true
		const out = expr(n)
		ctx.cond = was
		return out
	}

	function stmts(list) {
		const out = []
		for (const s of list) {
			if (ctx.count > MAX_STEPS) {
				out.push({ t: 'more' })
				break
			}
			out.push(...stmt(s))
		}
		return out
	}

	function stmt(s) {
		switch (s.kind) {
			case K.Block:
				return stmts(s.statements)
			case K.VariableStatement:
				return s.declarationList.declarations.flatMap((d) => {
					if (!d.initializer || byDecl.has(d)) return []
					const steps = expr(d.initializer)
					let target = unwrap(d.initializer)
					if (target?.kind === K.AwaitExpression) target = unwrap(target.expression)
					const hit = steps.find((x) => x._n === target)
					if (hit) hit.as = short(d.name, 50)
					return steps
				})
			case K.ExpressionStatement:
				return expr(s.expression)
			case K.IfStatement: {
				ctx.decisions++
				const cond = condSteps(s.expression)
				return [
					note({
						t: 'if',
						c: short(s.expression, 120),
						...(cond.length ? { cc: cond } : {}),
						yes: stmt(s.thenStatement),
						...(s.elseStatement ? { no: stmt(s.elseStatement) } : {}),
					}),
				]
			}
			case K.ReturnStatement:
				return [...expr(s.expression), retStep(s.expression)]
			case K.ThrowStatement:
				return [...expr(s.expression), note({ t: 'throw', v: short(s.expression, 120) })]
			case K.ForOfStatement:
			case K.ForInStatement:
			case K.ForStatement:
			case K.WhileStatement:
			case K.DoStatement: {
				ctx.decisions++
				const head =
					s.kind === K.ForOfStatement
						? `${short(s.initializer, 50)} of ${short(s.expression, 70)}`
						: s.kind === K.ForInStatement
							? `${short(s.initializer, 50)} in ${short(s.expression, 70)}`
							: s.kind === K.ForStatement
								? s.initializer || s.condition || s.incrementor
									? `${short(s.initializer, 40)}; ${short(s.condition, 50)}; ${short(s.incrementor, 30)}`
									: ''
								: short(s.expression, 100)
				const cond = condSteps(s.kind === K.ForStatement ? s.condition : s.expression)
				return [
					note({
						t: 'loop',
						c: head,
						w: s.kind === K.ForOfStatement || s.kind === K.ForInStatement ? 'each' : 'while',
						...(cond.length ? { cc: cond } : {}),
						body: stmt(s.statement),
					}),
				]
			}
			case K.TryStatement: {
				if (s.catchClause) ctx.decisions++
				return [
					note({
						t: 'try',
						body: stmt(s.tryBlock),
						...(s.catchClause
							? {
									catch: {
										v: s.catchClause.variableDeclaration
											? short(s.catchClause.variableDeclaration.name, 30)
											: '',
										body: stmt(s.catchClause.block),
									},
								}
							: {}),
						...(s.finallyBlock ? { fin: stmt(s.finallyBlock) } : {}),
					}),
				]
			}
			case K.SwitchStatement: {
				ctx.decisions += s.caseBlock.clauses.length
				return [
					...expr(s.expression),
					note({
						t: 'switch',
						c: short(s.expression, 80),
						cases: s.caseBlock.clauses.map((c) => ({
							c: c.kind === K.CaseClause ? short(c.expression, 60) : 'anything else',
							body: stmts(c.statements),
						})),
					}),
				]
			}
			case K.BreakStatement:
				return [note({ t: 'jump', v: 'break' })]
			case K.ContinueStatement:
				return [note({ t: 'jump', v: 'continue' })]
			case K.LabeledStatement:
				return stmt(s.statement)
			case K.FunctionDeclaration:
			case K.ClassDeclaration:
			case K.InterfaceDeclaration:
			case K.TypeAliasDeclaration:
			case K.EmptyStatement:
				return []
			default:
				return expr(s)
		}
	}

	function callStep(n) {
		const callee = n.expression
		const pre =
			callee.kind === K.PropertyAccessExpression
				? expr(callee.expression)
				: callee.kind === K.Identifier
					? []
					: expr(callee)
		const argSteps = []
		const cbs = []
		for (const a of n.arguments ?? []) {
			const u = unwrap(a)
			if (isFn(u) && !byFn.has(u)) {
				const b = body(u)
				if (b.length) cbs.push({ label: cbLabel(u), body: b })
			} else argSteps.push(...expr(a))
		}
		const target =
			callee.kind === K.Identifier || callee.kind === K.PropertyAccessExpression ? resolve(callee) : null
		const v = short(n, 110)
		const wait = awaited(n) ? { await: true } : {}
		let step = null
		if (target?.sym) {
			linkTo(target.sym, 'call')
			step = { t: 'call', id: target.sym.id, v, ...(target.via ? { via: target.via } : {}), ...wait }
		} else if (target?.param) {
			step = { t: 'call', param: target.param, v, ...wait }
		} else if (target?.ext) {
			const owner = callee.kind === K.PropertyAccessExpression ? callee.expression.getText(sf) : ''
			const first = n.arguments?.[0] && unwrap(n.arguments[0])
			if (ROUTE_LIBS.test(target.pkg) && /^(get|post|put|patch|delete|all|head|options|use)$/i.test(target.name) && first && ts.isStringLiteralLike(first) && first.text.startsWith('/')) {
				const handlers = n.arguments.slice(1).map((a) => {
					const u = unwrap(a)
					return u && (u.kind === K.Identifier || u.kind === K.PropertyAccessExpression) ? resolve(u)?.sym : null
				})
				routeRegs.push({ method: target.name.toUpperCase() === 'USE' ? 'ANY' : target.name.toUpperCase(), path: first.text, from: ctx.sym, handlers: handlers.filter(Boolean) })
			}
			const k = effectOf(target.pkg, target.name, owner)
			if (k) {
				const on = k.startsWith('db-') ? dbTarget(n) : undefined
				step = { t: 'fx', k, pkg: target.pkg, fn: target.name, v, ...(on ? { on } : {}), ...wait }
				ctx.effects.push({
					k,
					pkg: target.pkg,
					fn: target.name,
					...(on ? { on } : {}),
					line: lineOf(n.getStart(sf)),
				})
			}
		}
		if (!step) return [...pre, ...argSteps, ...cbs.map((c) => note({ t: 'cb', ...c }))]
		step._n = n
		if (cbs.length) step.cbs = cbs
		return [...pre, ...argSteps, note(step)]
	}

	function jsx(n) {
		const open = n.kind === K.JsxElement ? n.openingElement : n.kind === K.JsxSelfClosingElement ? n : null
		const inner = []
		if (open) {
			for (const a of open.attributes.properties) {
				if (a.kind === K.JsxSpreadAttribute) {
					inner.push(...expr(a.expression))
					continue
				}
				const e = a.initializer?.kind === K.JsxExpression ? a.initializer.expression : null
				if (!e) continue
				const u = unwrap(e)
				if (u.kind === K.Identifier || u.kind === K.PropertyAccessExpression) {
					const r = resolve(u)
					if (r?.sym?._fn) {
						linkTo(r.sym, 'use')
						inner.push(note({ t: 'use', id: r.sym.id, v: a.name.getText(sf) }))
						continue
					}
				}
				inner.push(...expr(e))
			}
		}
		for (const c of n.children ?? []) inner.push(...expr(c))
		const tag = open?.tagName
		if (tag && /^[A-Z]/.test(tag.getText(sf).split('.').pop())) {
			const r = resolve(tag)
			if (r?.sym) {
				linkTo(r.sym, 'render')
				return [
					note({
						t: 'render',
						id: r.sym.id,
						v: `<${tag.getText(sf)}>`,
						...(inner.length ? { kids: inner } : {}),
					}),
				]
			}
		}
		return inner
	}

	function expr(n) {
		if (!n || ctx.count > MAX_STEPS) return []
		switch (n.kind) {
			case K.ArrowFunction:
			case K.FunctionExpression: {
				if (byFn.has(n)) return []
				const b = body(n)
				return b.length ? [note({ t: 'cb', label: cbLabel(n), body: b })] : []
			}
			case K.CallExpression:
				return callStep(n)
			case K.NewExpression: {
				const r = ts.isIdentifier(n.expression) ? resolve(n.expression) : null
				const args = (n.arguments ?? []).flatMap((a) => expr(a))
				if (r?.sym) {
					linkTo(r.sym, 'call')
					return [...args, note({ t: 'call', id: r.sym.id, v: short(n, 110), new: true, _n: n })]
				}
				if (r?.ext && n.expression.getText(sf) === 'Response') {
					ctx.effects.push({ k: 'response', pkg: r.pkg, fn: 'Response', line: lineOf(n.getStart(sf)) })
					return [
						...args,
						note({ t: 'fx', k: 'response', pkg: r.pkg, fn: 'Response', v: short(n, 110), _n: n }),
					]
				}
				return args
			}
			case K.ConditionalExpression: {
				const cond = expr(n.condition)
				const a = expr(n.whenTrue)
				const b = expr(n.whenFalse)
				if (ctx.cond) return [...cond, ...a, ...b]
				if (!a.length && !b.length) return cond
				ctx.decisions++
				return [
					...cond,
					note({ t: 'if', c: short(n.condition, 120), x: true, yes: a, ...(b.length ? { no: b } : {}) }),
				]
			}
			case K.BinaryExpression: {
				const op = n.operatorToken.kind
				if (op === K.AmpersandAmpersandToken || op === K.BarBarToken || op === K.QuestionQuestionToken) {
					const l = expr(n.left)
					const r = expr(n.right)
					if (!r.length) return l
					ctx.decisions++
					if (ctx.cond) return [...l, ...r]
					const how =
						op === K.BarBarToken ? { unless: true } : op === K.QuestionQuestionToken ? { missing: true } : {}
					return [...l, note({ t: 'if', c: short(n.left, 120), ...how, x: true, yes: r })]
				}
				if (op === K.EqualsToken || op === K.QuestionQuestionEqualsToken || op === K.BarBarEqualsToken) {
					const steps = expr(n.right)
					let target = unwrap(n.right)
					if (target?.kind === K.AwaitExpression) target = unwrap(target.expression)
					const hit = steps.find((x) => x._n === target)
					if (hit) hit.as = short(n.left, 50)
					return [...expr(n.left), ...steps]
				}
				return [...expr(n.left), ...expr(n.right)]
			}
			case K.JsxElement:
			case K.JsxSelfClosingElement:
			case K.JsxFragment:
				return jsx(n)
			case K.PropertyAccessExpression: {
				const obj = n.expression
				if (ts.isIdentifier(obj) && obj.text === 'env') {
					const r = resolve(obj)
					if (r?.sym?.name === 'env' || /(^|\/)env\.[cm]?[jt]s$/.test(r?.sym?.file ?? '')) ctx.env.add(n.name.text)
				}
				if (obj.kind === K.PropertyAccessExpression && /^(process\.env|import\.meta\.env)$/.test(obj.getText(sf)))
					ctx.env.add(n.name.text)
				return expr(obj)
			}
			case K.Identifier: {
				const p = n.parent
				if (p && (p.kind === K.PropertyAssignment || p.kind === K.PropertyAccessExpression) && p.name === n)
					return []
				const r = resolve(n)
				if (r?.sym && r.sym !== ctx.sym && r.sym._fn) linkTo(r.sym, 'use')
				return []
			}
			case K.TypeReference:
			case K.TypeLiteral:
			case K.UnionType:
				return []
			default: {
				const out = []
				ts.forEachChild(n, (c) => {
					out.push(...expr(c))
				})
				return out
			}
		}
	}

	const clean = (steps) =>
		steps.map((s) => {
			const { _n, ...rest } = s
			for (const k of ['yes', 'no', 'body', 'kids', 'cc', 'fin'])
				if (Array.isArray(rest[k])) rest[k] = clean(rest[k])
			if (rest.catch) rest.catch = { ...rest.catch, body: clean(rest.catch.body) }
			if (rest.cases) rest.cases = rest.cases.map((c) => ({ ...c, body: clean(c.body) }))
			if (rest.cbs) rest.cbs = rest.cbs.map((c) => ({ ...c, body: clean(c.body) }))
			return rest
		})

	// ---------- signatures
	function typeRefs(node) {
		const out = new Set()
		const v = (n) => {
			if (n.kind === K.TypeReference) {
				const r = resolve(n.typeName.kind === K.QualifiedName ? n.typeName.right : n.typeName)
				if (r?.sym?.kind === 'type') out.add(r.sym.id)
			}
			ts.forEachChild(n, v)
		}
		if (node) v(node)
		return [...out]
	}
	function membersOf(typeNode) {
		const lit = typeNode && unwrap(typeNode)
		if (!lit || (lit.kind !== K.TypeLiteral && lit.kind !== K.InterfaceDeclaration)) return null
		return lit.members
			.filter((m) => m.name)
			.map((m) => ({
				name: nameText(m.name),
				type: m.type ? short(m.type, 140) : m.kind === K.MethodSignature ? 'function' : 'any',
				...(m.questionToken ? { opt: true } : {}),
				...(docOf(m).doc ? { doc: docOf(m).doc } : {}),
			}))
	}
	function paramsOf(fn, docParams) {
		return fn.parameters.map((p) => {
			const name = ts.isIdentifier(p.name) ? p.name.text : short(p.name, 60)
			const out = { name }
			if (p.dotDotDotToken) out.rest = true
			if (p.questionToken || p.initializer) out.opt = true
			if (p.initializer) out.def = short(p.initializer, 60)
			if (docParams[name]) out.doc = docParams[name]
			const refs = typeRefs(p.type)
			if (refs.length) out.refs = refs
			if (p.name.kind === K.ObjectBindingPattern) {
				const lit = membersOf(p.type)
				out.type = p.type && p.type.kind !== K.TypeLiteral ? short(p.type, 140) : 'an object'
				out.parts = p.name.elements.map((el) => {
					const key = nameText(el.propertyName ?? el.name)
					const m = lit?.find((x) => x.name === key)
					let t = m?.type
					if (!t)
						try {
							t = typeStr(checker.getTypeAtLocation(el.name))
						} catch {
							t = ''
						}
					return {
						name: key,
						type: t,
						...(el.initializer ? { def: short(el.initializer, 40), opt: true } : m?.opt ? { opt: true } : {}),
						...(m?.doc ? { doc: m.doc } : {}),
					}
				})
			} else {
				try {
					out.type = p.type ? short(p.type, 160) : typeStr(checker.getTypeAtLocation(p))
				} catch {
					out.type = ''
				}
			}
			return out
		})
	}
	function returnsOf(fn) {
		if (fn.type) return { returns: short(fn.type, 200), declaredReturn: true, retRefs: typeRefs(fn.type) }
		try {
			const sig = checker.getSignatureFromDeclaration(fn)
			return sig ? { returns: typeStr(checker.getReturnTypeOfSignature(sig)) } : {}
		} catch {
			return {}
		}
	}

	for (const sym of symbols) {
		sf = sym._sf
		checker = checkerOf.get(sym.file)
		ctx = { sym, count: 0, decisions: 0, links: new Map(), effects: [], env: new Set() }
		const docParams = sym.params ?? {}
		delete sym.params
		let outline = []
		if (sym._fn) {
			outline = body(sym._fn)
			sym.params = paramsOf(sym._fn, docParams)
			Object.assign(sym, returnsOf(sym._fn))
		} else if (sym._top) {
			outline = stmts(sym._top)
		} else if (sym.kind === 'type') {
			const d = sym._decl
			const members =
				d.kind === K.InterfaceDeclaration
					? membersOf(d)
					: d.kind === K.EnumDeclaration
						? d.members.map((m) => ({
								name: nameText(m.name),
								type: m.initializer ? short(m.initializer, 40) : '',
							}))
						: membersOf(d.type)
			if (members) sym.members = members
			else sym.value = short(d.type, 300)
		} else if (
			sym._init ||
			sym._decl.kind === K.VariableDeclaration ||
			sym._decl.kind === K.ExportAssignment
		) {
			const init =
				sym._init ?? (sym._decl.kind === K.ExportAssignment ? sym._decl.expression : sym._decl.initializer)
			if (init) {
				outline = expr(init)
				sym.value = short(init, 160)
				try {
					if (!sym.declared) sym.declared = typeStr(checker.getTypeAtLocation(sym._decl.name ?? init))
				} catch {}
			}
		} else if (sym.kind === 'class') {
			for (const m of sym._decl.members)
				if (m.kind === K.PropertyDeclaration && m.initializer) outline.push(...expr(m.initializer))
		}
		if (sym._top && !outline.length) sym._drop = true
		sym.outline = clean(outline)
		sym.links = [...ctx.links.entries()]
			.map(([id, how]) => ({ id, how }))
			.sort((a, b) => a.id.localeCompare(b.id))
		sym.effects = ctx.effects
		sym.env = [...ctx.env].sort()
		sym.decisions = ctx.decisions
	}

	// ------------------------------------------------------------ wiring: what config objects hook up
	const wiring = []
	function wire(owner, obj, at) {
		const o = unwrap(obj)
		if (!o) return
		if (o.kind === K.ObjectLiteralExpression) {
			for (const p of o.properties) {
				if (p.kind === K.ShorthandPropertyAssignment) {
					const r = resolve(p.name)
					if (r?.sym) wiring.push({ from: owner.id, to: r.sym.id, at: [...at, p.name.text].join('.') })
				} else if (p.kind === K.PropertyAssignment) wire(owner, p.initializer, [...at, nameText(p.name)])
			}
		} else if (o.kind === K.ArrayLiteralExpression) {
			for (const el of o.elements) {
				const u = unwrap(el)
				const named =
					u?.kind === K.ObjectLiteralExpression &&
					u.properties.find((p) => p.kind === K.PropertyAssignment && nameText(p.name) === 'name')
				const label = named && ts.isStringLiteral(named.initializer) ? `[${named.initializer.text}]` : null
				if (label && at.length) wire(owner, el, [...at.slice(0, -1), `${at.at(-1)}${label}`])
				else wire(owner, el, at)
			}
		} else if (o.kind === K.Identifier || o.kind === K.PropertyAccessExpression) {
			const r = resolve(o)
			if (r?.sym && r.sym !== owner && at.length)
				wiring.push({ from: owner.id, to: r.sym.id, at: at.join('.') })
		} else if (o.kind === K.CallExpression) {
			const r =
				ts.isIdentifier(o.expression) || o.expression.kind === K.PropertyAccessExpression
					? resolve(o.expression)
					: null
			if (r?.sym && at.length) wiring.push({ from: owner.id, to: r.sym.id, at: at.join('.'), made: true })
			for (const a of o.arguments) wire(owner, a, at)
		} else if (o.kind === K.SpreadAssignment || o.kind === K.SpreadElement) wire(owner, o.expression, at)
	}
	for (const sym of symbols) {
		if (sym._fn || sym._top || sym.kind === 'type' || sym.kind === 'class') continue
		sf = sym._sf
		checker = checkerOf.get(sym.file)
		const init =
			sym._init ?? (sym._decl.kind === K.ExportAssignment ? sym._decl.expression : sym._decl.initializer)
		wire(sym, init, [])
	}
	// A plain function hooked up as a Payload hook, access rule or check takes that role.
	for (const w of wiring) {
		const to = symbols.find((s) => s.id === w.to)
		if (to?.kind !== 'function') continue
		if (/(^|\.)hooks\./.test(w.at)) to.kind = 'hook'
		else if (/(^|\.)access\./.test(w.at)) to.kind = 'access'
		else if (/(^|\.)validate$/.test(w.at)) to.kind = 'validate'
	}

	// ------------------------------------------------------------ entry points
	const triggers = new Map()
	const addEntry = (sym, kind, trigger) => {
		if (!triggers.has(sym.id)) triggers.set(sym.id, { id: sym.id, file: sym.file, kind, list: [] })
		triggers.get(sym.id).list.push(trigger)
	}
	for (const s of symbols) {
		const url = routeUrl(s.file)
		const base = path.posix.basename(s.file).replace(/\.[cm]?[jt]sx?$/, '')
		let trigger = null
		if (s.kind === 'page') trigger = /^(not-found)$/.test(base) ? `no page matches${url === '/' ? '' : ` under ${url}`}` : /error$/.test(base) ? `an error under ${url}` : url
		else if (s.kind === 'layout') trigger = `every page under ${url}`
		else if (s.kind === 'endpoint' && /^(robots|sitemap|manifest)$/.test(base)) trigger = `GET /${base}${base === 'robots' ? '.txt' : base === 'manifest' ? '.webmanifest' : '.xml'}`
		else if (s.kind === 'endpoint' && /(^|\/)pages\/api\//.test(s.file)) trigger = `ANY ${url}`
		else if (s.kind === 'endpoint' && HTTP.has(s.name)) trigger = `${s.name} ${url}`
		else if (s.kind === 'meta') trigger = url
		else if (s.kind === 'proxy') trigger = 'every request, before any page'
		else if (s.kind === 'startup') trigger = 'once, when the server starts'
		else if (s.kind === 'action') trigger = 'a form or button in the browser'
		else if (s.kind === 'task') {
			sf = s._sf
			const text = s._decl.initializer?.getText(sf) ?? ''
			const slug = text.match(/slug:\s*'([^']+)'/)?.[1]
			const cron = text.match(/cron:\s*'([^']+)'/)?.[1]
			trigger = `background task ${slug ?? s.name}${cron ? ` (cron ${cron})` : ''}`
		} else if (s.kind === 'script') {
			const hit = scriptFor(s.file)
			trigger = hit ? (hit.cmd.startsWith('bin ') ? `the ${hit.name} command` : runCmd(hit.pk, hit.name)) : 'run by hand'
		} else if (['hook', 'access', 'validate'].includes(s.kind)) {
			const w = wiring.filter((x) => x.to === s.id)
			if (w.length) trigger = w.map((x) => `${byId.get(x.from)?.name} · ${x.at}`).join('; ')
		}
		if (trigger) addEntry(s, s.kind, trigger)
	}
	// Routes registered in code (`app.get('/x', handler)`): the handler is the entry point, or the code that registers
	// an inline one.
	for (const r of routeRegs) {
		const label = `${r.method} ${r.path}`
		if (r.handlers.length) for (const h of r.handlers) {
			if (h.kind === 'function') h.kind = 'endpoint'
			addEntry(h, 'endpoint', label)
		}
		else addEntry(r.from, 'endpoint', `${label} (inline handler)`)
	}
	const entries = [...triggers.values()].map(({ list, ...e }) => ({ ...e, trigger: [...new Set(list)].join('; ') }))

	// ------------------------------------------------------------ tests: which checks use which function
	const tests = {}
	for (const file of testFiles) {
		sf = sourceOf.get(file)
		checker = checkerOf.get(file)
		if (!sf) continue
		const seen = (id, title) => {
			tests[id] ||= []
			const list = tests[id]
			if (!list.some((t) => t.file === file && t.title === title)) list.push({ file, title })
		}
		const visit = (n, title) => {
			let t = title
			if (
				n.kind === K.CallExpression &&
				ts.isIdentifier(n.expression) &&
				/^(it|test)$/.test(n.expression.text)
			) {
				const a = n.arguments[0]
				if (a && ts.isStringLiteralLike(a)) t = a.text
			}
			if (
				n.kind === K.Identifier &&
				n.parent?.kind !== K.ImportSpecifier &&
				n.parent?.kind !== K.ImportClause
			) {
				const r = resolve(n)
				if (r?.sym) seen(r.sym.id, t)
			}
			ts.forEachChild(n, (c) => visit(c, t))
		}
		visit(sf, null)
	}
	for (const list of Object.values(tests))
		list.sort((a, b) => a.file.localeCompare(b.file) || String(a.title).localeCompare(String(b.title)))

	// ------------------------------------------------------------ out
	const out = symbols
		.filter((s) => !s._drop)
		.map((s) => {
			const { _decl, _fn, _sf, _top, _drop, _init, directive, ...rest } = s
			if (!rest.doc) delete rest.doc
			if (!rest.exported) delete rest.exported
			if (!rest.isDefault) delete rest.isDefault
			if (!rest.async) delete rest.async
			if (directive) rest.runs = directive === 'use client' ? 'browser' : 'server action'
			for (const k of ['outline', 'links', 'effects', 'env'])
				if (Array.isArray(rest[k]) && !rest[k].length) delete rest[k]
			if (!rest.decisions) delete rest.decisions
			return rest
		})
		.sort((a, b) => a.file.localeCompare(b.file) || a.line - b.line || a.id.localeCompare(b.id))
	wiring.sort((a, b) => a.from.localeCompare(b.from) || a.at.localeCompare(b.at) || a.to.localeCompare(b.to))
	entries.sort((a, b) => a.kind.localeCompare(b.kind) || a.trigger.localeCompare(b.trigger))
	return { projects: projects.map(({ name, root }) => ({ name, root })), symbols: out, entries, wiring, tests, sources }
}

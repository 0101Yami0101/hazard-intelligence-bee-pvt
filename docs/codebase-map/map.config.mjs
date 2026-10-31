// Settings for the codebase map scanner (scripts/codebase-map/scan.mjs). Detected by the codebase-map skill; edit freely.
export default {
	mapDir: 'docs/codebase-map',
	// TypeScript/JavaScript projects the Functions tab reads: one per tsconfig/jsconfig. Each may add
	// include: [path prefixes] and exclude: [path prefixes or '/regex/'] to narrow what's mapped.
	code: [],
	// Extra import aliases on top of each tsconfig's `paths`, e.g. { '@/': 'src/' }.
	aliases: {},
	// [regex source, kind] pairs that override the built-in file kinds
	// (app, test, migration, config, ci, doc, design, infra, tooling).
	kinds: [
		// This is a data pipeline: the Python under scripts/ is the product's own code, not tooling.
		['^scripts/(?!codebase-map/).*\\.py$', 'app'],
	],
	// Generated files (drawn dashed, never described by hand): path prefixes or '/regex/'.
	generated: [],
	envExample: '.env.example',
	// A file whose `NAME:` keys list the env vars the app checks at startup (e.g. a Zod schema).
	envSchema: null,
	// Python code is read for os.environ / os.getenv. Add the project's own helpers whose first string argument
	// names an env var, e.g. ['credential'] for credential("API_KEY").
	envReaders: ['credential'],
	// Python for the Functions tab, read with Python's own parser (any Python 3.8+; the repo's .venv is tried first):
	// { enabled: false } turns it off; interpreter: a path; include/exclude: path prefixes or '/regex/';
	// paths: extra import roots (e.g. ['src']) when imports don't resolve from the file's folder or its sys.path setup.
	python: {},
	// The rules shown on the Safety tab: the bullets under this heading.
	rules: { file: null, heading: 'Hard rules' },
	// Database tables are found in Drizzle/Payload snapshots, Prisma schemas or .sql files. Point at one source if
	// several exist: { snapshots: 'src/migrations' } · { prisma: 'prisma/schema.prisma' } · { sql: 'supabase/migrations' }
	schema: {},
}

import { readdirSync, mkdirSync } from 'node:fs';
import { join, relative, sep } from 'node:path';
import { spawnSync } from 'node:child_process';
function walk(dir) { return readdirSync(dir, {withFileTypes:true}).flatMap(e => e.isDirectory() ? walk(join(dir,e.name)) : [join(dir,e.name)]); }
const files = walk('docs').filter(p => p.endsWith('.mmd'));
mkdirSync('build/diagrams', {recursive:true});
for (const file of files) {
 const output = join('build/diagrams', relative('docs',file).split(sep).join('-') + '.svg');
 const result = spawnSync(process.execPath, ['node_modules/@mermaid-js/mermaid-cli/src/cli.js','-i',file,'-o',output,'-p','scripts/puppeteer.json'], {stdio:'inherit'});
 if (result.status !== 0) process.exit(result.status ?? 1);
}
console.log(`Rendered ${files.length} Mermaid diagrams`);

import {mkdtempSync, writeFileSync, rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {spawnSync} from 'node:child_process';
const dir = mkdtempSync(join(tmpdir(), 'lab2-mermaid-'));
try {
 const file = join(dir,'invalid.mmd');
 writeFileSync(file, 'flowchart LR\n A[broken --> B[unclosed');
 const result = spawnSync(process.execPath,['node_modules/@mermaid-js/mermaid-cli/src/cli.js','-i',file,'-o',join(dir,'out.svg'),'-p','scripts/puppeteer.json'],{encoding:'utf8'});
 const output = (result.stdout ?? '') + (result.stderr ?? '');
 if (result.status === 0 || !/parse error|syntax error/i.test(output)) {
  console.error(output); throw new Error('Expected a Mermaid syntax rejection');
 }
 console.log('PASS: intentionally malformed Mermaid rejected with parse error');
} finally { rmSync(dir,{recursive:true,force:true}); }

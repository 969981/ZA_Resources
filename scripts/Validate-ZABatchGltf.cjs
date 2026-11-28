// Validate every emitted GLB; failures are recorded per model and fail the job.
const fs=require("fs"),path=require("path"),validator=require("gltf-validator");
const walk=p=>fs.readdirSync(p,{withFileTypes:true}).flatMap(x=>x.isDirectory()?walk(path.join(p,x.name)):x.name.endsWith(".glb")?[path.join(p,x.name)]:[]);
(async()=>{const root=process.argv[2],rows=[];
for(const f of walk(root).sort()){const r=await validator.validateBytes(new Uint8Array(fs.readFileSync(f)),{uri:path.basename(f),maxIssues:100});rows.push({file:path.relative(root,f),errors:r.issues.numErrors,warnings:r.issues.numWarnings,infos:r.issues.numInfos,messages:r.issues.messages});}
fs.writeFileSync(path.join(root,"khronos-summary.json"),JSON.stringify(rows,null,2));
console.log("K_BATCH",JSON.stringify(rows.map(({file,errors,warnings,infos})=>({file,errors,warnings,infos}))));
if(!rows.length||rows.some(r=>r.errors))process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=1});

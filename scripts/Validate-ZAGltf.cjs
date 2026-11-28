// Official Khronos npm validator. Explicitly fail any errors; preserve warnings.
const fs=require("fs");
const path=require("path");
const validator=require("gltf-validator");
(async()=>{
  const root=process.argv[2];
  const rows=[];
  for(const name of fs.readdirSync(root).filter(n=>n.endsWith(".glb")).sort()){
    const result=await validator.validateBytes(new Uint8Array(fs.readFileSync(path.join(root,name))),{uri:name,maxIssues:100});
    rows.push({file:name,issues:result.issues,info:result.info});
  }
  fs.writeFileSync(path.join(root,"khronos-summary.json"),JSON.stringify(rows,null,2));
  console.log("KHRONOS",JSON.stringify(rows.map(r=>({file:r.file,errors:r.issues.numErrors,warnings:r.issues.numWarnings,infos:r.issues.numInfos}))));
  if(rows.length!==2||rows.some(r=>r.issues.numErrors))process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=1;});

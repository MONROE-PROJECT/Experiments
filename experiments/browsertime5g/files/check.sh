#!/usr/bin/bash
  
cat > expected_output <<- "EOF"
< var glob=require("glob");
< var fs=require("fs");
< glob("/tmp/rust_mozprofile*", function(er, files) {
< console.log(files[0]);
< if (fs.existsSync(files[0])){
< fs.rename(files[0],"/opt/monroe/profile_moz", function(err){
< if (err) console.log("Error: "+ err);
< });
< }
< });
EOF

sed '/^  async stop() {/a var glob=require("glob");\nvar fs=require("fs");\nglob("/tmp/rust_mozprofile*", function(er, files) {\nconsole.log(files[0]);\nif (fs.existsSync(files[0])){\nfs.rename(files[0],"/opt/monroe/profile_moz", function(err){\nif (err) console.log("Error: "+ err);\n});\n}\n});' /usr/src/app/lib/core/seleniumRunner.js > changed.js

diff --normal changed.js /usr/src/app/lib/core/seleniumRunner.js| egrep "^<" > diff_result


STATUS="$(cmp --silent expected_output diff_result; echo $?)"
if [[ $STATUS -ne 0 ]]; then  echo "FAILURE"; else     cp changed.js /usr/src/app/lib/core/seleniumRunner.js ; fi

// extract.js
const fs = require("fs");
const vm = require("vm");

// Get the filename from command-line arguments
const filename = process.argv[2];

if (!filename) {
  console.error("Usage: node extract.js <path-to-js-file>");
  process.exit(1);
}

// Read the JS file as text
const code = fs.readFileSync(filename, "utf8");

// Create a sandbox with an exports object
const sandbox = { exports: {} };
vm.createContext(sandbox);

// Run the JS file inside the sandbox
vm.runInContext(code, sandbox);

// Print the exported object as JSON
console.log(JSON.stringify(sandbox.exports));
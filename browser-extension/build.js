const fs = require('fs-extra');
const path = require('path');
const archiver = require('archiver');
const { execSync } = require('child_process');

// Configuration
const BUILD_DIR = path.join(__dirname, 'build');
const TARGET_BROWSERS = ['chrome', 'firefox', 'opera'];

// Clean build directory
function cleanBuildDir() {
  console.log('Cleaning build directory...');
  if (fs.existsSync(BUILD_DIR)) {
    fs.removeSync(BUILD_DIR);
  }
  fs.mkdirpSync(BUILD_DIR);
}

// Read and parse manifest
function getManifest(browser) {
  const manifestPath = path.join(__dirname, 'manifest.json');
  let manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
  
  // Browser-specific modifications
  switch (browser) {
    case 'firefox':
      // Firefox specific settings
      manifest.browser_specific_settings = {
        gecko: {
          id: 'password-manager@example.com',
          strict_min_version: '91.0'
        }
      };
      break;
      
    case 'opera':
      // Opera specific settings
      manifest.minimum_opera_version = '80.0';
      break;
      
    // Chrome/Edge use the base manifest
  }
  
  return manifest;
}

// Copy extension files
function copyExtensionFiles(browser, targetDir) {
  console.log(`Copying files for ${browser}...`);
  
  // Create target directory
  fs.mkdirpSync(targetDir);
  
  // Copy common files
  const filesToCopy = [
    'background.js',
    'content.js',
    'popup.js',
    'popup.html',
    'icons/'
  ];
  
  filesToCopy.forEach(file => {
    const src = path.join(__dirname, file);
    const dest = path.join(targetDir, file);
    
    if (fs.existsSync(src)) {
      if (fs.lstatSync(src).isDirectory()) {
        fs.copySync(src, dest);
      } else {
        fs.copyFileSync(src, dest);
      }
    }
  });
  
  // Write browser-specific manifest
  const manifest = getManifest(browser);
  fs.writeFileSync(
    path.join(targetDir, 'manifest.json'),
    JSON.stringify(manifest, null, 2)
  );
}

// Create ZIP archive
function createZipArchive(sourceDir, targetFile) {
  console.log(`Creating archive: ${targetFile}`);
  
  return new Promise((resolve, reject) => {
    const output = fs.createWriteStream(targetFile);
    const archive = archiver('zip', { zlib: { level: 9 } });
    
    output.on('close', () => {
      console.log(`Created ${targetFile} (${archive.pointer()} bytes)`);
      resolve();
    });
    
    archive.on('error', (err) => {
      reject(err);
    });
    
    archive.pipe(output);
    archive.directory(sourceDir, false);
    archive.finalize();
  });
}

// Build extension for a specific browser
async function buildForBrowser(browser) {
  console.log(`\nBuilding for ${browser}...`);
  
  const browserDir = path.join(BUILD_DIR, browser);
  const zipFile = path.join(BUILD_DIR, `password-manager-${browser}.zip`);
  
  // Copy files
  copyExtensionFiles(browser, browserDir);
  
  // Create ZIP archive
  await createZipArchive(browserDir, zipFile);
  
  console.log(`✅ ${browser} extension built successfully`);
  return { browser, path: browserDir, zip: zipFile };
}

// Main build function
async function build() {
  try {
    console.log('Starting extension build process...');
    
    // Clean and prepare
    cleanBuildDir();
    
    // Build for each target browser
    const results = [];
    for (const browser of TARGET_BROWSERS) {
      const result = await buildForBrowser(browser);
      results.push(result);
    }
    
    console.log('\n🎉 All extensions built successfully!');
    console.log('\nBuild output:');
    results.forEach(({ browser, path, zip }) => {
      console.log(`- ${browser}: ${path}\n  ZIP: ${zip}`);
    });
    
  } catch (error) {
    console.error('\n❌ Build failed:', error);
    process.exit(1);
  }
}

// Run the build
build();

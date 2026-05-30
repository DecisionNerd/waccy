const { existsSync, readFileSync } = require('fs')
const { join } = require('path')

const { platform, arch } = process

let nativeBinding = null
let loadError = null

function isMusl() {
  if (!process.report || typeof process.report.getReport !== 'function') {
    try {
      const lddPath = require('child_process').execSync('which ldd').toString().trim()
      return readFileSync(lddPath, 'utf8').includes('musl')
    } catch {
      return true
    }
  }
  const { glibcVersionRuntime } = process.report.getReport().header
  return !glibcVersionRuntime
}

switch (platform) {
  case 'darwin':
    switch (arch) {
      case 'x64':
        nativeBinding = require('./waccy.darwin-x64.node')
        break
      case 'arm64':
        nativeBinding = require('./waccy.darwin-arm64.node')
        break
      default:
        throw new Error(`Unsupported macOS architecture: ${arch}`)
    }
    break
  case 'linux':
    switch (arch) {
      case 'x64':
        if (isMusl()) {
          nativeBinding = require('./waccy.linux-x64-musl.node')
        } else {
          nativeBinding = require('./waccy.linux-x64-gnu.node')
        }
        break
      case 'arm64':
        if (isMusl()) {
          nativeBinding = require('./waccy.linux-arm64-musl.node')
        } else {
          nativeBinding = require('./waccy.linux-arm64-gnu.node')
        }
        break
      default:
        throw new Error(`Unsupported Linux architecture: ${arch}`)
    }
    break
  default:
    throw new Error(`Unsupported platform: ${platform}`)
}

module.exports = nativeBinding

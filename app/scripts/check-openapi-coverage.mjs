import { readdir, readFile } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'

const specificationPath = fileURLToPath(new URL('../../docs/openapi.json', import.meta.url))
const apiDirectory = fileURLToPath(new URL('../src/services/api/', import.meta.url))
const specification = JSON.parse(await readFile(specificationPath, 'utf8'))
const httpMethods = ['get', 'post', 'put', 'patch', 'delete']

// These endpoints persist runtime/log data or provide detail variants not currently
// initiated by a management page. Keeping them explicit makes new operations fail
// coverage until they are either wired to a frontend service or acknowledged here.
const backendOnlyOperations = new Set([
  'POST /api/v1/conversations',
  'PUT /api/v1/conversations/{*}',
  'DELETE /api/v1/conversations/{*}',
  'POST /api/v1/conversations/{*}/turns',
  'POST /api/v1/turns/{*}/trace',
  'PUT /api/v1/conversations/{*}/annotation',
  'GET /api/v1/system/api-keys/{*}',
  'PUT /api/v1/system/alerts/{*}',
])

const normalizePath = (path) => {
  const normalized = path
    .replace(/\$\{[^}]+\}/g, '{*}')
    .replace(/\{[^}]+\}/g, '{*}')
    .replace(/\/$/, '')
  return normalized || '/'
}

const serviceOperations = new Set(['GET /health'])
for (const fileName of await readdir(apiDirectory)) {
  if (!fileName.endsWith('.ts')) continue
  const source = await readFile(`${apiDirectory}/${fileName}`, 'utf8')
  const callPattern = /apiClient\.(getBlob|get|post|put|patch|delete)[^(]*\(\s*[`'"]([^`'"]+)[`'"]/g
  for (const match of source.matchAll(callPattern)) {
    const method = match[1] === 'getBlob' ? 'GET' : match[1].toUpperCase()
    serviceOperations.add(`${method} ${normalizePath(`/api/v1${match[2]}`)}`)
  }
}

const specificationOperations = new Set()
for (const [path, operations] of Object.entries(specification.paths ?? {})) {
  for (const method of httpMethods) {
    if (operations[method]) specificationOperations.add(`${method.toUpperCase()} ${normalizePath(path)}`)
  }
}

const registeredOperations = new Set([...serviceOperations, ...backendOnlyOperations])
const missing = [...specificationOperations].filter((operation) => !registeredOperations.has(operation))
const staleBackendOnly = [...backendOnlyOperations].filter((operation) => !specificationOperations.has(operation))

if (missing.length || staleBackendOnly.length) {
  if (missing.length) console.error(`OpenAPI 新增但前端服务未登记：\n- ${missing.join('\n- ')}`)
  if (staleBackendOnly.length) console.error(`后端专用清单中已不存在的接口：\n- ${staleBackendOnly.join('\n- ')}`)
  process.exitCode = 1
} else {
  console.log(`OpenAPI coverage: ${specificationOperations.size}/${specificationOperations.size} operations registered (${backendOnlyOperations.size} backend-only)`)
}

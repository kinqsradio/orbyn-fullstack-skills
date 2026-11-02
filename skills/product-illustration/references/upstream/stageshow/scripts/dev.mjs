#!/usr/bin/env node
// Serves the playground with plain Vite on 127.0.0.1, in this working copy.
import { spawn } from 'node:child_process'
import { existsSync, realpathSync } from 'node:fs'
import { constants } from 'node:os'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..')

export function devCommand(extra = []) {
  const vite = resolve(root, 'node_modules', 'vite', 'bin', 'vite.js')
  if (!existsSync(vite)) throw new Error(`Vite is missing; run npm install --ignore-scripts in ${root}`)
  return { command: process.execPath, args: [vite, 'playground', '--config', 'playground/vite.config.ts', '--host', '127.0.0.1', ...extra], cwd: root }
}

function main() {
  let command
  try { command = devCommand(process.argv.slice(2)) } catch (error) {
    console.error(`Stageshow: ${error.message}`)
    process.exitCode = 1
    return
  }
  const child = spawn(command.command, command.args, { cwd: command.cwd, stdio: 'inherit', shell: false })
  const handlers = new Map(['SIGINT', 'SIGTERM'].map((signal) => [signal, () => {
    if (child.exitCode === null && child.signalCode === null) child.kill(signal)
  }]))
  for (const [signal, handler] of handlers) process.on(signal, handler)
  const cleanup = () => { for (const [signal, handler] of handlers) process.removeListener(signal, handler) }
  child.once('error', (error) => {
    cleanup()
    console.error(`Stageshow: could not start the dev server: ${error.message}`)
    process.exitCode = 1
  })
  child.once('close', (code, signal) => {
    cleanup()
    process.exitCode = typeof code === 'number' && code >= 0 ? code : signal ? 128 + (constants.signals[signal] ?? 1) : 1
  })
}

if (process.argv[1] && realpathSync(process.argv[1]) === fileURLToPath(import.meta.url)) main()

/**
 * Block Registry — single source of truth for supported block types.
 *
 * To add a new block type:
 *   1. Create a BlockHandler implementation
 *   2. Call `registry.register(handler)` or pass it to `createRegistry(handlers)`
 *
 * The compiler queries the registry to validate and extract data from graph nodes.
 */

import type { BlockHandler } from "./types.js";

export class BlockRegistry {
  private readonly handlers = new Map<string, BlockHandler>();

  /** Register a handler. Throws if the blockType is already registered. */
  register(handler: BlockHandler): void {
    if (this.handlers.has(handler.blockType)) {
      throw new Error(`BlockRegistry: duplicate handler for "${handler.blockType}"`);
    }
    this.handlers.set(handler.blockType, handler);
  }

  /** Get a handler by block type, or undefined if not registered. */
  get(blockType: string): BlockHandler | undefined {
    return this.handlers.get(blockType);
  }

  /** Check if a block type is registered. */
  has(blockType: string): boolean {
    return this.handlers.has(blockType);
  }

  /** All registered block types. */
  registeredTypes(): string[] {
    return [...this.handlers.keys()];
  }

  /** All registered handlers. */
  allHandlers(): BlockHandler[] {
    return [...this.handlers.values()];
  }
}

/**
 * Factory: create a registry pre-populated with a list of handlers.
 */
export function createRegistry(handlers: BlockHandler[]): BlockRegistry {
  const registry = new BlockRegistry();
  for (const h of handlers) {
    registry.register(h);
  }
  return registry;
}

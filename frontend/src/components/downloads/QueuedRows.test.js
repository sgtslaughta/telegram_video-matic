import { describe, expect, it } from 'vitest';
import { moveItem } from './data';
describe('moveItem', () => {
    it('moves an item to a new index', () => {
        expect(moveItem([1, 2, 3, 4], 3, 0)).toEqual([4, 1, 2, 3]);
        expect(moveItem([1, 2, 3, 4], 0, 2)).toEqual([2, 3, 1, 4]);
    });
});

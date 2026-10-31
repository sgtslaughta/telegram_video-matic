import { describe, expect, it } from 'vitest';
import { outageSpans } from './spans';
const c = (down = 0, error = 0) => ({ t: '', ok: 1, error, down, queued: 0 });
describe('outageSpans', () => {
    it('merges consecutive outage hours and splits by kind', () => {
        expect(outageSpans([c(), c(1), c(1), c(), c(0, 2), c(1)])).toEqual([
            { from: 1, to: 2, kind: 'down' }, { from: 4, to: 4, kind: 'error' }, { from: 5, to: 5, kind: 'down' },
        ]);
    });
});

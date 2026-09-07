import test from 'node:test';
import assert from 'node:assert/strict';

import { factCheckPresentation } from './factCheckPresentation.js';


test('describes a matched published review without treating it as the model verdict', () => {
  assert.deepEqual(
    factCheckPresentation({
      status: 'matched',
      claim: 'A claim',
      rating: 'False',
      publisher: 'FactCheck.org',
      url: 'https://example.com/review',
    }),
    {
      tone: 'positive',
      title: 'Published fact-check found',
      detail: 'FactCheck.org rated a related claim “False”.',
      linkLabel: 'Open source',
      url: 'https://example.com/review',
    },
  );
});


test('makes a missing review explicit rather than implying the claim is true', () => {
  assert.equal(
    factCheckPresentation({ status: 'not_found' }).detail,
    'No published review matched this text. This does not establish that it is true or false.',
  );
});


test('explains that a temporary lookup failure is not evidence', () => {
  assert.equal(
    factCheckPresentation({ status: 'unavailable' }).title,
    'Fact-check lookup unavailable',
  );
});

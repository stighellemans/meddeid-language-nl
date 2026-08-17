import assert from 'node:assert/strict';
import test from 'node:test';

import { subannotationProfile } from '../js/subannotation-profile.js';

function apply(ruleId, category, text, item = {}) {
  const rule = subannotationProfile.rules.find((candidate) => candidate.ruleId === ruleId);
  return rule.transformSegment({
    item,
    text,
    segment: { begin: 0, end: Array.from(text).length, category },
  });
}

test('profile identity and resources align with the Python nl-BE profile', () => {
  assert.equal(subannotationProfile.contractVersion, 'meddeid.subannotation-profile.v1');
  assert.equal(subannotationProfile.profileId, 'nl-BE');
  assert.equal(subannotationProfile.profileVersion, '1');
  assert.equal(subannotationProfile.resourceManifest.profile_id, 'nl-BE');
  assert.equal(subannotationProfile.implementation.sha256.length, 64);
  assert.ok(subannotationProfile.resourceManifest.resources.first_names.values > 10_000);
});

test('Dutch date and age expressions receive semantic categories', () => {
  const date = apply('split_dutch_date_variants', 'datetime_identifier', '18 juli 2026');
  assert.deepEqual(date.map((segment) => segment.category), [
    'day', 'formatting', 'month', 'formatting', 'year',
  ]);
  const age = apply('split_dutch_date_variants', 'datetime_identifier', '7-jarige');
  assert.deepEqual(age.map((segment) => segment.category), [
    'age_year', 'formatting', 'age_type',
  ]);
});

test('packaged name and Belgian address resources drive suggestions', () => {
  const name = apply('split_name_variants_from_profile', 'name_identifier', 'Jan Peeters');
  assert.deepEqual(name.map((segment) => segment.category), [
    'given', 'formatting', 'family',
  ]);
  const address = apply(
    'split_address_organization_variants_from_profile',
    'address_identifier',
    'Kerkstraat 14, 9000 Gent',
  );
  assert.ok(address.some((segment) => segment.category === 'street'));
  assert.ok(address.some((segment) => segment.category === 'postal_code'));
  assert.ok(address.some((segment) => segment.category === 'municipality'));
});

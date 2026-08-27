import assert from 'node:assert/strict';
import test from 'node:test';

import { subannotationProfile as belgianProfile } from '../js/subannotation-nl-be.js';
import { subannotationProfile as netherlandsProfile } from '../js/subannotation-nl-nl.js';

let subannotationProfile = belgianProfile;

function apply(ruleId, category, text, item = {}) {
  const rule = subannotationProfile.rules.find((candidate) => candidate.ruleId === ruleId);
  return rule.transformSegment({
    item,
    text,
    segment: { begin: 0, end: Array.from(text).length, category },
  });
}

test('both profiles expose unversioned, profile-scoped resources', () => {
  for (const [profile, profileId] of [
    [belgianProfile, 'nl-BE'],
    [netherlandsProfile, 'nl-NL'],
  ]) {
    assert.equal(profile.contractVersion, 'meddeid.subannotation-profile.v1');
    assert.equal(profile.profileId, profileId);
    assert.equal(Object.hasOwn(profile, 'profile' + 'Version'), false);
    assert.equal(profile.resourceManifest.profile_id, profileId);
    assert.equal(profile.implementation.sha256.length, 64);
    assert.ok(profile.resourceManifest.resources.first_names.values > 10_000);
  }
});

test('Dutch date and age expressions receive semantic categories', () => {
  const date = apply('split_dutch_date_variants', subannotationProfile.seedCategories.Date, '18 juli 2026');
  assert.deepEqual(date.map((segment) => segment.category), [
    'day', 'formatting', 'month', 'formatting', 'year',
  ]);
  const age = apply('split_dutch_date_variants', subannotationProfile.seedCategories.Age_Birthdate, '7-jarige');
  assert.deepEqual(age.map((segment) => segment.category), [
    'age_year', 'formatting', 'age_type',
  ]);
});

test('packaged name and Belgian address resources drive suggestions', () => {
  subannotationProfile = belgianProfile;
  const name = apply('split_name_variants_from_profile', subannotationProfile.seedCategories.Name, 'Jan Peeters');
  assert.deepEqual(name.map((segment) => segment.category), [
    'given', 'formatting', 'family',
  ]);
  const address = apply(
    'split_address_organization_variants_from_profile',
    subannotationProfile.seedCategories.Address_Location,
    'Kerkstraat 14, 9000 Gent',
  );
  assert.ok(address.some((segment) => segment.category === 'street'));
  assert.ok(address.some((segment) => segment.category === 'postal_code'));
  assert.ok(address.some((segment) => segment.category === 'municipality'));
});

test('Netherlands resources drive suggestions for the same Dutch rules', () => {
  subannotationProfile = netherlandsProfile;
  const address = apply(
    'split_address_organization_variants_from_profile',
    subannotationProfile.seedCategories.Address_Location,
    'Damrak 1, 1012 Amsterdam',
  );
  assert.ok(address.some((segment) => segment.category === 'street'));
  assert.ok(address.some((segment) => segment.category === 'postal_code'));
  assert.ok(address.some((segment) => segment.category === 'municipality'));
});

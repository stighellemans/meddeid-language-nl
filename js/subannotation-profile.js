/**
 * nl-BE semantic subannotation capability.
 *
 * This module intentionally owns language/locale interpretation while the
 * application owns offsets, persistence, review state, and rule execution.
 * It reads the same packaged resources as the Python LanguageProfile.
 */
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const MODULE_DIR = path.dirname(fileURLToPath(import.meta.url));
const MODULE_PATH = fileURLToPath(import.meta.url);
const LOOKUP_DIR = path.resolve(
  MODULE_DIR,
  '..',
  'src',
  'meddeid_language_nl',
  'resources',
  'lookup',
);
const PROFILE_SPEC = JSON.parse(fs.readFileSync(path.resolve(
  MODULE_DIR,
  '..',
  'src',
  'meddeid_language_nl',
  'resources',
  'subannotation',
  'profile.json',
), 'utf8'));

const LOOKUP_FILES = Object.freeze({
  first_names: 'first_names.txt',
  family_names: 'family_names.txt',
  prefixes: 'prefixes.txt',
  interfixes: 'interfixes.txt',
  interfix_surnames: 'interfix_surnames.txt',
  streets: 'streets.txt',
  localities: 'localities.txt',
  postal_localities: 'postal_localities.txt',
  postal_code_localities: 'postal_code_localities.txt',
  hospitals: 'hospitals.txt',
  healthcare_institutions: 'healthcare_institutions.txt',
});

function normalize(value) {
  return String(value ?? '').normalize('NFKC').trim().toLocaleLowerCase('nl');
}

function readLookup(category) {
  const filename = LOOKUP_FILES[category];
  if (!filename) throw new Error(`Unknown nl-BE lookup category: ${category}`);
  return fs.readFileSync(path.join(LOOKUP_DIR, filename), 'utf8')
    .split(/\r?\n/u)
    .map((line) => line.trim())
    .filter((line) => line && !line.startsWith('#'));
}

function lookupSet(category) {
  return new Set(readLookup(category).map(normalize));
}

function tokenize(value) {
  const chars = Array.from(String(value ?? ''));
  const tokens = [];
  let cursor = 0;
  while (cursor < chars.length) {
    const start = cursor;
    const isLetter = /\p{L}/u.test(chars[cursor]);
    const isDigit = /\d/u.test(chars[cursor]);
    cursor += 1;
    while (cursor < chars.length) {
      if (isLetter && /[\p{L}\p{M}'’]/u.test(chars[cursor])) cursor += 1;
      else if (isDigit && /\d/u.test(chars[cursor])) cursor += 1;
      else if (!isLetter && !isDigit && !/[\p{L}\p{M}\d]/u.test(chars[cursor])) cursor += 1;
      else break;
    }
    const raw = chars.slice(start, cursor).join('');
    tokens.push({
      begin: start,
      end: cursor,
      raw,
      normalized: normalize(raw),
      kind: isLetter ? 'word' : isDigit ? 'number' : 'formatting',
    });
  }
  return tokens;
}

function createPhraseTrie(values) {
  const root = new Map();
  for (const value of values) {
    const words = tokenize(value).filter((token) => token.kind !== 'formatting');
    if (!words.length) continue;
    let node = root;
    for (const word of words) {
      if (!node.has(word.normalized)) node.set(word.normalized, new Map());
      node = node.get(word.normalized);
    }
    node.terminal = true;
  }
  return root;
}

function longestPhraseAt(tokens, semanticIndex, trie) {
  let node = trie;
  let best = 0;
  let semanticCount = 0;
  for (let index = semanticIndex; index < tokens.length; index += 1) {
    const token = tokens[index];
    if (token.kind === 'formatting') continue;
    node = node.get(token.normalized);
    if (!node) break;
    semanticCount += 1;
    if (node.terminal) best = semanticCount;
  }
  return best;
}

const FIRST_NAMES = lookupSet('first_names');
const FAMILY_NAMES = lookupSet('family_names');
const INTERFIXES = lookupSet('interfixes');
const PREFIX_TRIE = createPhraseTrie(readLookup('prefixes'));
const STREET_TRIE = createPhraseTrie(readLookup('streets'));
const LOCALITY_TRIE = createPhraseTrie(readLookup('localities'));
const HOSPITAL_TRIE = createPhraseTrie([
  ...readLookup('hospitals'),
  ...readLookup('healthcare_institutions'),
]);

const DUTCH_MONTHS = new Set([
  'januari', 'februari', 'maart', 'april', 'mei', 'juni', 'juli', 'augustus',
  'september', 'oktober', 'november', 'december', 'jan', 'feb', 'mrt', 'apr',
  'jun', 'jul', 'aug', 'sep', 'okt', 'nov', 'dec',
]);
const DUTCH_WEEKDAYS = new Set([
  'maandag', 'dinsdag', 'woensdag', 'donderdag', 'vrijdag', 'zaterdag', 'zondag',
  'ma', 'di', 'wo', 'do', 'vr', 'za', 'zo',
]);
const DUTCH_SEASONS = new Set(['lente', 'zomer', 'herfst', 'winter']);
const AGE_UNITS = new Map([
  ['jaar', 'age_year'], ['jaren', 'age_year'], ['jarige', 'age_year'],
  ['maand', 'age_month'], ['maanden', 'age_month'], ['mnd', 'age_month'],
  ['week', 'age_week'], ['weken', 'age_week'], ['wk', 'age_week'],
  ['dag', 'age_day'], ['dagen', 'age_day'],
]);

function absoluteSegments(segment, tokens, categories) {
  return tokens.map((token, index) => ({
    begin: segment.begin + token.begin,
    end: segment.begin + token.end,
    category: token.kind === 'formatting'
      ? 'formatting'
      : categories[index] ?? segment.category,
  }));
}

function semanticNeighbors(tokens, index) {
  let previous = index - 1;
  while (previous >= 0 && tokens[previous].kind === 'formatting') previous -= 1;
  let next = index + 1;
  while (next < tokens.length && tokens[next].kind === 'formatting') next += 1;
  return { previous, next };
}

function parseDutchDate({ segment, text }) {
  const tokens = tokenize(text);
  const categories = [];
  const semantic = tokens.map((token, index) => ({ token, index }))
    .filter(({ token }) => token.kind !== 'formatting');

  for (let position = 0; position < semantic.length; position += 1) {
    const { token, index } = semantic[position];
    const next = semantic[position + 1];
    if (token.kind === 'number' && next && AGE_UNITS.has(next.token.normalized)) {
      categories[index] = AGE_UNITS.get(next.token.normalized);
      categories[next.index] = 'age_type';
      continue;
    }
    if (AGE_UNITS.has(token.normalized)) {
      categories[index] = 'age_type';
    } else if (DUTCH_MONTHS.has(token.normalized)) {
      categories[index] = 'month';
    } else if (DUTCH_WEEKDAYS.has(token.normalized)) {
      categories[index] = 'weekday';
    } else if (DUTCH_SEASONS.has(token.normalized)) {
      categories[index] = 'season';
    }
  }

  for (let position = 0; position + 2 < semantic.length; position += 1) {
    const triplet = semantic.slice(position, position + 3);
    if (!triplet.every(({ token }) => token.kind === 'number')) continue;
    const [day, month, year] = triplet;
    const dayNumber = Number(day.token.raw);
    const monthNumber = Number(month.token.raw);
    if (dayNumber >= 1 && dayNumber <= 31 && monthNumber >= 1 && monthNumber <= 12) {
      categories[day.index] = 'day';
      categories[month.index] = 'month';
      categories[year.index] = 'year';
      break;
    }
  }

  for (const { token, index } of semantic) {
    if (categories[index] || token.kind !== 'number') continue;
    const number = Number(token.raw);
    const { previous, next } = semanticNeighbors(tokens, index);
    if (token.raw.length === 4 && number >= 1800 && number <= 2200) {
      categories[index] = 'year';
    } else if (next < tokens.length && DUTCH_MONTHS.has(tokens[next].normalized) && number <= 31) {
      categories[index] = 'day';
    } else if (previous >= 0 && DUTCH_MONTHS.has(tokens[previous].normalized)) {
      categories[index] = token.raw.length === 4 ? 'year' : 'day';
    }
  }

  return absoluteSegments(segment, tokens, categories);
}

function parseName({ item, segment, text }) {
  const tokens = tokenize(text);
  const categories = [];
  const semanticIndices = tokens.map((token, index) => ({ token, index }))
    .filter(({ token }) => token.kind !== 'formatting')
    .map(({ index }) => index);

  const metadataGiven = normalize(item?.metadata?.patientGivenName);
  const metadataFamily = normalize(item?.metadata?.patientLastName);
  for (let position = 0; position < semanticIndices.length; position += 1) {
    const index = semanticIndices[position];
    const token = tokens[index];
    const prefixLength = longestPhraseAt(tokens, index, PREFIX_TRIE);
    if (prefixLength > 0 && position === 0) {
      let remaining = prefixLength;
      for (let cursor = index; cursor < tokens.length && remaining > 0; cursor += 1) {
        if (tokens[cursor].kind !== 'formatting') {
          categories[cursor] = 'title';
          remaining -= 1;
        }
      }
      continue;
    }
    if (token.normalized === metadataGiven || FIRST_NAMES.has(token.normalized)) {
      categories[index] = 'given';
    }
    if (token.normalized === metadataFamily || FAMILY_NAMES.has(token.normalized)) {
      if (!categories[index] || position === semanticIndices.length - 1) categories[index] = 'family';
    }
    if (INTERFIXES.has(token.normalized)) categories[index] = 'family';
    if (Array.from(token.raw).length === 1) categories[index] = 'initials';
  }
  return absoluteSegments(segment, tokens, categories);
}

function applyPhraseCategory(tokens, categories, trie, category) {
  for (let index = 0; index < tokens.length; index += 1) {
    if (tokens[index].kind === 'formatting' || categories[index]) continue;
    const length = longestPhraseAt(tokens, index, trie);
    if (!length) continue;
    let remaining = length;
    for (let cursor = index; cursor < tokens.length && remaining > 0; cursor += 1) {
      if (tokens[cursor].kind !== 'formatting') {
        categories[cursor] = category;
        remaining -= 1;
      }
    }
  }
}

function parseAddressOrOrganization({ segment, text }) {
  const tokens = tokenize(text);
  const categories = [];
  if (segment.category === 'organization_identifier') {
    applyPhraseCategory(tokens, categories, HOSPITAL_TRIE, 'institution');
  } else {
    applyPhraseCategory(tokens, categories, STREET_TRIE, 'street');
    applyPhraseCategory(tokens, categories, LOCALITY_TRIE, 'municipality');
    for (let index = 0; index < tokens.length; index += 1) {
      const token = tokens[index];
      if (token.kind !== 'number' || categories[index]) continue;
      if (token.raw.length === 4 && Number(token.raw) >= 1000) {
        categories[index] = 'postal_code';
      } else {
        const previousSemantic = tokens.slice(0, index).reverse()
          .findIndex((candidate) => candidate.kind !== 'formatting');
        categories[index] = previousSemantic >= 0 ? 'house_number' : segment.category;
      }
    }
  }
  return absoluteSegments(segment, tokens, categories);
}

function parseContact({ segment, text }) {
  const compact = String(text).trim();
  const digits = compact.replace(/\D/gu, '');
  if (!compact.includes('@') && /^[+\d\s()./-]+$/u.test(compact) && digits.length >= 4) {
    const category = digits.length === 4 ? 'internal_phone' : 'public_phone';
    return absoluteSegments(segment, tokenize(text), []).map((part) => ({
      ...part,
      category: part.category === 'formatting' ? 'formatting' : category,
    }));
  }
  if (compact.includes('@')) {
    const tokens = tokenize(text);
    const categories = tokens.map((token) => {
      if (token.kind === 'formatting') return 'formatting';
      if (FIRST_NAMES.has(token.normalized)) return 'given';
      if (FAMILY_NAMES.has(token.normalized)) return 'family';
      return 'additional_info';
    });
    return absoluteSegments(segment, tokens, categories);
  }
  return null;
}

const RULES = Object.freeze([
  Object.freeze({
    ruleId: 'split_dutch_date_variants',
    transformSegment({ item, segment, text }) {
      return segment.category === 'datetime_identifier'
        ? parseDutchDate({ item, segment, text })
        : null;
    },
  }),
  Object.freeze({
    ruleId: 'split_name_variants_from_profile',
    transformSegment({ item, segment, text }) {
      return segment.category === 'name_identifier'
        ? parseName({ item, segment, text })
        : null;
    },
  }),
  Object.freeze({
    ruleId: 'split_address_organization_variants_from_profile',
    transformSegment({ segment, text }) {
      return ['address_identifier', 'organization_identifier'].includes(segment.category)
        ? parseAddressOrOrganization({ segment, text })
        : null;
    },
  }),
  Object.freeze({
    ruleId: 'split_contact_variants',
    transformSegment({ segment, text }) {
      return segment.category === 'contact_identifier'
        ? parseContact({ segment, text })
        : null;
    },
  }),
  Object.freeze({
    ruleId: 'classify_identifier_content',
    transformSegment({ segment }) {
      return segment.category === 'id_identifier'
        ? [{ ...segment, category: 'internal_id' }]
        : null;
    },
  }),
]);

function resourceManifest() {
  const resources = {};
  for (const [category, filename] of Object.entries(LOOKUP_FILES)) {
    const content = fs.readFileSync(path.join(LOOKUP_DIR, filename));
    resources[category] = {
      filename,
      sha256: crypto.createHash('sha256').update(content).digest('hex'),
      values: readLookup(category).length,
    };
  }
  return {
    manifest_version: 'meddeid.language-resources.v1',
    package: 'meddeid-language-nl',
    package_version: '0.1.0',
    profile_id: 'nl-BE',
    profile_version: '1',
    resources,
  };
}

export const subannotationProfile = Object.freeze({
  ...PROFILE_SPEC,
  rules: RULES,
  resourceManifest: resourceManifest(),
  implementation: Object.freeze({
    package: '@meddeid/language-nl',
    export: './subannotation',
    sha256: crypto.createHash('sha256').update(fs.readFileSync(MODULE_PATH)).digest('hex'),
  }),
});

export default subannotationProfile;

// Chord Transposition Logic for Worship Songs App

// Define the chromatic scale
const CHROMATIC_SCALE = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
const FLAT_SCALE = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B'];

// Common chord patterns
const CHORD_PATTERNS = {
    // Major chords
    'maj': '',
    'major': '',
    'M': '',
    
    // Minor chords
    'min': 'm',
    'minor': 'm',
    'm': 'm',
    
    // Seventh chords
    '7': '7',
    'maj7': 'maj7',
    'M7': 'M7',
    'm7': 'm7',
    'min7': 'm7',
    
    // Other common chords
    'dim': 'dim',
    'aug': 'aug',
    'sus2': 'sus2',
    'sus4': 'sus4',
    'add9': 'add9',
    '9': '9',
    '11': '11',
    '13': '13'
};

/**
 * Parse a chord string to extract root note and chord type
 * @param {string} chord - The chord string (e.g., "Gm7", "C#sus4")
 * @returns {object} - Object with root and suffix properties
 */
function parseChord(chord) {
    if (!chord || typeof chord !== 'string') {
        return { root: '', suffix: '' };
    }
    
    chord = chord.trim();
    
    // Handle sharp and flat notes
    let root = '';
    let suffix = '';
    
    if (chord.length >= 2 && (chord[1] === '#' || chord[1] === 'b')) {
        root = chord.substring(0, 2);
        suffix = chord.substring(2);
    } else if (chord.length >= 1) {
        root = chord[0];
        suffix = chord.substring(1);
    }
    
    return { root: root.toUpperCase(), suffix };
}

/**
 * Transpose a single chord by a given number of semitones
 * @param {string} chord - The chord to transpose
 * @param {number} semitones - Number of semitones to transpose (positive = up, negative = down)
 * @returns {string} - The transposed chord
 */
function transposeChord(chord, semitones) {
    if (!chord || typeof chord !== 'string') {
        return chord;
    }
    
    const { root, suffix } = parseChord(chord);
    
    if (!root) {
        return chord;
    }
    
    // Find the root note in the chromatic scale
    let rootIndex = CHROMATIC_SCALE.indexOf(root);
    
    // If not found in sharp scale, try flat scale
    if (rootIndex === -1) {
        rootIndex = FLAT_SCALE.indexOf(root);
        if (rootIndex === -1) {
            return chord; // Invalid chord, return as is
        }
    }
    
    // Calculate new index with proper wrapping
    let newIndex = (rootIndex + semitones) % 12;
    if (newIndex < 0) {
        newIndex += 12;
    }
    
    // Determine whether to use sharp or flat based on the original chord
    let newRoot;
    if (FLAT_SCALE.includes(root)) {
        newRoot = FLAT_SCALE[newIndex];
    } else {
        newRoot = CHROMATIC_SCALE[newIndex];
    }
    
    return newRoot + suffix;
}

/**
 * Format lyrics text with chord highlighting - simple line-by-line display
 * @param {string} lyrics - Raw lyrics text with chords in [chord] format or separate lines
 * @returns {string} - HTML formatted lyrics preserving line structure
 */
function formatLyricsWithChords(lyrics) {
    if (!lyrics || typeof lyrics !== 'string') {
        return '';
    }
    
    // Split lyrics into lines for processing
    const lines = lyrics.split('\n');
    const formattedLines = [];
    
    lines.forEach((line, index) => {
        if (line.trim() === '') {
            formattedLines.push('<div class="empty-line">&nbsp;</div>');
            return;
        }
        
        // Check if this line contains only chords (like [Dm7] or multiple chords)
        const onlyChordPattern = /^[\s\[\]A-Ga-g#b0-9maj-]+$/;
        const hasChordBrackets = /\[[^\]]+\]/;
        
        if (hasChordBrackets.test(line)) {
            // If line has chord brackets, format them
            const formattedLine = line.replace(/\[([^\]]+)\]/g, function(match, chord) {
                return `<span class="chord" data-original-chord="${chord}">${chord}</span>`;
            });
            
            // Check if this is a chord-only line or mixed content
            const lineWithoutChords = line.replace(/\[([^\]]+)\]/g, '');
            if (lineWithoutChords.trim() === '' || lineWithoutChords.trim().match(/^[\s-]+$/)) {
                // This is primarily a chord line
                formattedLines.push(`<div class="chord-line-simple">${formattedLine}</div>`);
            } else {
                // This has mixed chords and lyrics
                formattedLines.push(`<div class="lyrics-line">${formattedLine}</div>`);
            }
        } else {
            // Regular text line
            formattedLines.push(`<div class="lyrics-line">${line}</div>`);
        }
    });
    
    return formattedLines.join('');
}

/**
 * Extract all chords from lyrics text
 * @param {string} lyrics - Raw lyrics text with chords in [chord] format
 * @returns {Array} - Array of unique chords found in the lyrics
 */
function extractChords(lyrics) {
    if (!lyrics || typeof lyrics !== 'string') {
        return [];
    }
    
    const chordMatches = lyrics.match(/\[([^\]]+)\]/g) || [];
    const chords = chordMatches.map(match => match.slice(1, -1)); // Remove brackets
    
    // Return unique chords
    return [...new Set(chords)];
}

/**
 * Transpose all chords in a lyrics string
 * @param {string} lyrics - Raw lyrics text with chords in [chord] format
 * @param {number} semitones - Number of semitones to transpose
 * @returns {string} - Lyrics with transposed chords
 */
function transposeLyrics(lyrics, semitones) {
    if (!lyrics || typeof lyrics !== 'string' || semitones === 0) {
        return lyrics;
    }
    
    return lyrics.replace(/\[([^\]]+)\]/g, function(match, chord) {
        const transposedChord = transposeChord(chord, semitones);
        return `[${transposedChord}]`;
    });
}

/**
 * Get the key signature for a given root note
 * @param {string} key - The key (e.g., "C", "G", "F#")
 * @returns {object} - Object with key signature information
 */
function getKeySignature(key) {
    const keySignatures = {
        'C': { sharps: 0, flats: 0, accidentals: [] },
        'G': { sharps: 1, flats: 0, accidentals: ['F#'] },
        'D': { sharps: 2, flats: 0, accidentals: ['F#', 'C#'] },
        'A': { sharps: 3, flats: 0, accidentals: ['F#', 'C#', 'G#'] },
        'E': { sharps: 4, flats: 0, accidentals: ['F#', 'C#', 'G#', 'D#'] },
        'B': { sharps: 5, flats: 0, accidentals: ['F#', 'C#', 'G#', 'D#', 'A#'] },
        'F#': { sharps: 6, flats: 0, accidentals: ['F#', 'C#', 'G#', 'D#', 'A#', 'E#'] },
        'F': { sharps: 0, flats: 1, accidentals: ['Bb'] },
        'Bb': { sharps: 0, flats: 2, accidentals: ['Bb', 'Eb'] },
        'Eb': { sharps: 0, flats: 3, accidentals: ['Bb', 'Eb', 'Ab'] },
        'Ab': { sharps: 0, flats: 4, accidentals: ['Bb', 'Eb', 'Ab', 'Db'] },
        'Db': { sharps: 0, flats: 5, accidentals: ['Bb', 'Eb', 'Ab', 'Db', 'Gb'] },
        'Gb': { sharps: 0, flats: 6, accidentals: ['Bb', 'Eb', 'Ab', 'Db', 'Gb', 'Cb'] }
    };
    
    return keySignatures[key] || { sharps: 0, flats: 0, accidentals: [] };
}

/**
 * Suggest the best enharmonic equivalent for a chord based on key context
 * @param {string} chord - The chord to check
 * @param {string} key - The key context
 * @returns {string} - The best enharmonic equivalent
 */
function getEnharmonicEquivalent(chord, key) {
    const { root, suffix } = parseChord(chord);
    const keySignature = getKeySignature(key);
    
    // Enharmonic equivalents
    const enharmonics = {
        'C#': 'Db', 'Db': 'C#',
        'D#': 'Eb', 'Eb': 'D#',
        'F#': 'Gb', 'Gb': 'F#',
        'G#': 'Ab', 'Ab': 'G#',
        'A#': 'Bb', 'Bb': 'A#'
    };
    
    // If the key signature suggests flats and we have a sharp, convert to flat
    if (keySignature.flats > 0 && root.includes('#') && enharmonics[root]) {
        return enharmonics[root] + suffix;
    }
    
    // If the key signature suggests sharps and we have a flat, convert to sharp
    if (keySignature.sharps > 0 && root.includes('b') && enharmonics[root]) {
        return enharmonics[root] + suffix;
    }
    
    return chord;
}

// Export functions for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        transposeChord,
        formatLyricsWithChords,
        extractChords,
        transposeLyrics,
        parseChord,
        getKeySignature,
        getEnharmonicEquivalent,
        CHROMATIC_SCALE,
        FLAT_SCALE
    };
}

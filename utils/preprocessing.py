import re
import string
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Standard English stop words fallback list in case NLTK download fails
DEFAULT_STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", 
    "aren't", "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", 
    "but", "by", "can", "can't", "cannot", "could", "couldn't", "did", "didn't", "do", "does", 
    "doesn't", "doing", "don't", "down", "during", "each", "few", "for", "from", "further", 
    "had", "hadn't", "has", "hasn't", "have", "haven't", "having", "he", "he'd", "he'll", "he's", 
    "her", "here", "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i", 
    "i'd", "i'll", "i'm", "i'ive", "if", "in", "into", "is", "isn't", "it", "it's", "its", 
    "itself", "let's", "me", "more", "most", "mustn't", "my", "myself", "no", "nor", "not", 
    "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours", "ourselves", 
    "out", "over", "own", "same", "shan't", "she", "she'd", "she'll", "she's", "should", 
    "shouldn't", "so", "some", "such", "than", "that", "that's", "the", "their", "theirs", 
    "them", "themselves", "then", "there", "there's", "these", "they", "they'd", "they'll", 
    "they're", "they've", "this", "those", "through", "to", "too", "under", "until", "up", 
    "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were", "weren't", 
    "what", "what's", "when", "when's", "where", "where's", "which", "while", "who", 
    "who's", "whom", "why", "why's", "with", "won't", "would", "wouldn't", "you", "you'd", 
    "you'll", "you're", "you've", "your", "yours", "yourself", "yourselves"
}

# Initialize NLTK components safely
try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize
    from nltk.stem import WordNetLemmatizer

    # Download required datasets if missing
    for resource in ['punkt', 'stopwords', 'wordnet', 'punkt_tab']:
        try:
            nltk.download(resource, quiet=True)
        except Exception as e:
            logger.warning(f"NLTK download failed for {resource}: {e}")

    try:
        STOP_WORDS = set(stopwords.words('english'))
    except Exception:
        STOP_WORDS = DEFAULT_STOPWORDS

    try:
        lemmatizer = WordNetLemmatizer()
    except Exception:
        lemmatizer = None

    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
    STOP_WORDS = DEFAULT_STOPWORDS
    lemmatizer = None
    logger.warning("NLTK is not installed. Using fallback regex tokenization.")


def clean_text(text: str) -> str:
    """
    Cleans input text by:
    1. Lowercasing
    2. Removing HTML tags
    3. Removing punctuation & special characters
    4. Normalizing whitespace
    """
    if not text or not isinstance(text, str):
        return ""
    
    # 1. Lowercase
    text = text.lower().strip()
    
    # 2. Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)
    
    # 3. Remove punctuation and special characters
    text = re.sub(r'[' + re.escape(string.punctuation) + ']', ' ', text)
    
    # 4. Remove extra spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def tokenize(text: str) -> list:
    """
    Tokenizes clean text into individual words using NLTK word_tokenize
    or regex fallback.
    """
    if not text:
        return []
        
    if NLTK_AVAILABLE:
        try:
            return word_tokenize(text)
        except Exception:
            pass
            
    # Fallback tokenization
    return text.split()


def remove_stopwords(tokens: list) -> list:
    """
    Removes stop words from token list.
    """
    return [token for token in tokens if token not in STOP_WORDS and len(token) > 1]


def lemmatize_tokens(tokens: list) -> list:
    """
    Applies lemmatization to tokens if WordNetLemmatizer is available.
    """
    if not tokens:
        return []
        
    if lemmatizer:
        try:
            return [lemmatizer.lemmatize(token) for token in tokens]
        except Exception:
            pass
            
    return tokens


def preprocess_text(text: str) -> str:
    """
    Full NLP Preprocessing Pipeline:
    Input string -> Lowercase/Clean -> Tokenize -> Remove Stopwords -> Lemmatize -> Processed String
    """
    # Step 1: Clean text
    cleaned = clean_text(text)
    if not cleaned:
        return ""
        
    # Step 2: Tokenize
    tokens = tokenize(cleaned)
    
    # Step 3: Stopword removal
    filtered_tokens = remove_stopwords(tokens)
    
    # If all tokens were removed as stopwords (e.g. "what is it"), keep clean tokens
    if not filtered_tokens and tokens:
        filtered_tokens = tokens
        
    # Step 4: Lemmatization
    lemmatized = lemmatize_tokens(filtered_tokens)
    
    # Step 5: Join back to processed string
    return " ".join(lemmatized)


if __name__ == "__main__":
    sample_q = "How CAN I track my ORDER???"
    processed = preprocess_text(sample_q)
    print(f"Original: {sample_q}")
    print(f"Processed: '{processed}'")

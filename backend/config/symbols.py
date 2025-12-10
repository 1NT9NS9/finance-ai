"""
Symbol definitions for all financial instruments tracked by the system.
Organized by data source and category for easy management.
"""

# =============================================================================
# MOSCOW EXCHANGE SYMBOLS
# =============================================================================

# Russian market index
MOEX_INDEX = {
    "IMOEX": {
        "name": "Moscow Exchange Index",
        "sector": "Index",
        "board": "SNDX",
        "engine": "index",  # Changed to index engine
        "type": "index"
    }
}

# Oil and gas sector
MOEX_OIL_GAS = {
    "RTGZ": {
        "name": "Rosneft Oil Company",
        "sector": "Oil and Gas",
        "board": "TQBR",
        "engine": "stock"
    }
}

# Electric power sector
MOEX_ELECTRIC_POWER = {
    "MRKV": {
        "name": "IDGC of Volga",
        "sector": "Electric Power",
        "board": "TQBR",
        "engine": "stock"
    },
    "MRKC": {
        "name": "IDGC of Centre",
        "sector": "Electric Power",
        "board": "TQBR",
        "engine": "stock"
    },
    "KRSB": {
        "name": "Krasnoyarskenergo",
        "sector": "Electric Power",
        "board": "TQBR",
        "engine": "stock"
    }
}

# Telecom sector
MOEX_TELECOM = {
    "MTSS": {
        "name": "Mobile TeleSystems",
        "sector": "Telecom",
        "board": "TQBR",
        "engine": "stock"
    }
}

# Metallurgy and mining sector
MOEX_METALLURGY_MINING = {
    "PLZL": {
        "name": "Polyus Gold",
        "sector": "Metallurgy and Mining",
        "board": "TQBR",
        "engine": "stock"
    }
    # POLY removed - no longer traded
}

# Consumer sector
MOEX_CONSUMER = {
    "LENT": {
        "name": "Lenta Ltd",
        "sector": "Consumer",
        "board": "TQBR",
        "engine": "stock"
    }
}

# Finance sector
MOEX_FINANCE = {
    "SBER": {
        "name": "Sberbank of Russia",
        "sector": "Finance",
        "board": "TQBR",
        "engine": "stock"
    },
    "T": {  # Corrected back to T ticker
        "name": "TCS Group Holding",
        "sector": "Finance",
        "board": "TQBR",
        "engine": "stock"
    }
}

# Information technology sector
MOEX_IT = {
    "OZON": {
        "name": "Ozon Holdings",
        "sector": "IT",
        "board": "TQBR",
        "engine": "stock"
    },
    "YDEX": {  # Corrected to YDEX ticker
        "name": "Yandex N.V.",
        "sector": "IT",
        "board": "TQBR",
        "engine": "stock"
    }
}

# Combine all MOEX symbols
MOEX_SYMBOLS = {
    **MOEX_INDEX,
    **MOEX_OIL_GAS,
    **MOEX_ELECTRIC_POWER,
    **MOEX_TELECOM,
    **MOEX_METALLURGY_MINING,
    **MOEX_CONSUMER,
    **MOEX_FINANCE,
    **MOEX_IT
}

# =============================================================================
# YAHOO FINANCE SYMBOLS
# =============================================================================

# Cryptocurrencies
YAHOO_CRYPTO = {
    "BTC-USD": {
        "name": "Bitcoin",
        "category": "Cryptocurrency",
        "base_currency": "USD"
    },
    "ETH-USD": {
        "name": "Ethereum",
        "category": "Cryptocurrency",
        "base_currency": "USD"
    },
    "SOL-USD": {
        "name": "Solana",
        "category": "Cryptocurrency",
        "base_currency": "USD"
    }
}

# Precious metals
YAHOO_METALS = {
    "XAUT-USD": {
        "name": "Gold",
        "category": "Precious Metals",
        "base_currency": "USD"
    }
}

# Indices
YAHOO_INDICES = {
    "^SPX": {
        "name": "S&P 500",
        "category": "Index",
        "base_currency": "USD"
    }
}

# Combine all Yahoo Finance symbols
YAHOO_SYMBOLS = {
    **YAHOO_CRYPTO,
    **YAHOO_METALS,
    **YAHOO_INDICES
}

# =============================================================================
# COMPLETE SYMBOL LISTS
# =============================================================================

# All symbols by source
ALL_MOEX_SYMBOLS = list(MOEX_SYMBOLS.keys())
ALL_YAHOO_SYMBOLS = list(YAHOO_SYMBOLS.keys())

# All symbols combined
ALL_SYMBOLS = ALL_MOEX_SYMBOLS + ALL_YAHOO_SYMBOLS

# Symbol validation sets
VALID_MOEX_SYMBOLS = set(ALL_MOEX_SYMBOLS)
VALID_YAHOO_SYMBOLS = set(ALL_YAHOO_SYMBOLS)
VALID_ALL_SYMBOLS = set(ALL_SYMBOLS)

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_symbol_info(symbol: str) -> dict:
    """
    Get detailed information about a symbol.
    
    Args:
        symbol (str): Symbol to get information for
        
    Returns:
        dict: Symbol information or empty dict if not found
    """
    if symbol in MOEX_SYMBOLS:
        return MOEX_SYMBOLS[symbol]
    elif symbol in YAHOO_SYMBOLS:
        return YAHOO_SYMBOLS[symbol]
    else:
        return {}

def get_symbols_by_sector(sector: str) -> list:
    """
    Get all symbols belonging to a specific sector.
    
    Args:
        sector (str): Sector name to filter by
        
    Returns:
        list: List of symbols in the sector
    """
    symbols = []
    for symbol, info in MOEX_SYMBOLS.items():
        if info.get("sector", "").lower() == sector.lower():
            symbols.append(symbol)
    return symbols

def get_symbols_by_category(category: str) -> list:
    """
    Get all symbols belonging to a specific category (for Yahoo Finance).
    
    Args:
        category (str): Category name to filter by
        
    Returns:
        list: List of symbols in the category
    """
    symbols = []
    for symbol, info in YAHOO_SYMBOLS.items():
        if info.get("category", "").lower() == category.lower():
            symbols.append(symbol)
    return symbols

def is_moex_symbol(symbol: str) -> bool:
    """Check if symbol is from Moscow Exchange."""
    return symbol in VALID_MOEX_SYMBOLS

def is_yahoo_symbol(symbol: str) -> bool:
    """Check if symbol is from Yahoo Finance."""
    return symbol in VALID_YAHOO_SYMBOLS
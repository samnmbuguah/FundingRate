import React, { useState } from 'react';

interface CryptoLogoProps {
    symbol: string;
    size?: number;
}

const CryptoLogo: React.FC<CryptoLogoProps> = ({ symbol, size = 24 }) => {
    const [error, setError] = useState(false);

    // Clean symbol (remove USD, USDT, etc. if needed, but Lighter symbols seem clean)
    // Lighter symbols are like "ETH", "BTC", "SOL".
    // Using a public CDN for crypto icons.
    const logoUrl = `https://lcw.nyc3.cdn.digitaloceanspaces.com/production/currencies/64/${symbol.toLowerCase()}.png`;

    if (error) {
        return (
            <div
                style={{
                    width: size,
                    height: size,
                    borderRadius: '50%',
                    backgroundColor: '#334155',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: size * 0.5,
                    color: '#94a3b8',
                    fontWeight: 'bold'
                }}
            >
                {symbol.charAt(0)}
            </div>
        );
    }

    return (
        <img
            src={logoUrl}
            alt={`${symbol} logo`}
            width={size}
            height={size}
            onError={() => setError(true)}
            style={{ borderRadius: '50%', objectFit: 'cover' }}
        />
    );
};

export default CryptoLogo;

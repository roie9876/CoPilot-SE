import { useState } from 'react';

function AppTest() {
  const [count, setCount] = useState(0);

  return (
    <div style={{ padding: '20px', backgroundColor: '#f0f0f0', minHeight: '100vh' }}>
      <h1 style={{ color: 'black', fontSize: '48px' }}>Test Page</h1>
      <p style={{ color: 'black', fontSize: '24px' }}>If you see this, React is working!</p>
      <button 
        onClick={() => setCount(count + 1)}
        style={{ 
          padding: '10px 20px', 
          fontSize: '18px', 
          backgroundColor: 'blue', 
          color: 'white',
          border: 'none',
          borderRadius: '5px',
          cursor: 'pointer'
        }}
      >
        Count: {count}
      </button>
    </div>
  );
}

export default AppTest;

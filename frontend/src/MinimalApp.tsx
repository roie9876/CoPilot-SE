function MinimalApp() {
  return (
    <div style={{ 
      padding: '50px', 
      backgroundColor: '#f0f0f0',
      minHeight: '100vh',
      fontSize: '24px',
      color: 'black'
    }}>
      <h1 style={{ fontSize: '48px', color: 'red', marginBottom: '20px' }}>
        MINIMAL APP LOADED
      </h1>
      <p>If you see this, the problem is with the complex App component.</p>
      <p>Current time: {new Date().toLocaleTimeString()}</p>
    </div>
  );
}

export default MinimalApp;

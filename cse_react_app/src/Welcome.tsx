import './CSEAppCommon'
import React from 'react'

function Welcome()
{
  const [isVisible, setIsVisible] = React.useState(false);
  React.useEffect(() => { setIsVisible(true); }, []);
  return (
    <div className="flex items-center justify-center min-h-screen min-w-screen bg-gradient-to-br from-primary_bg to-secondary_bg">
      <div
        className={`text-center transition-opacity duration-1000 ${
          isVisible ? 'opacity-100' : 'opacity-0'
        }`}
      >
        <h1 className="text-4xl md:text-5xl font-bold text-primary_text mb-4">
          Welcome To Cyber Syn Eve!
        </h1>
        <p className="text-lg md:text-xl text-primary_text mb-6">
          Loading...
        </p>
        <div className="flex justify-center space-x-2">
          <div className="w-3 h-3 bg-primary_text rounded-full animate-bounce" style={{ animationDelay: '0s' }}></div>
          <div className="w-3 h-3 bg-primary_text rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
          <div className="w-3 h-3 bg-primary_text rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
        </div>
      </div>
    </div>
  )
}

export default Welcome
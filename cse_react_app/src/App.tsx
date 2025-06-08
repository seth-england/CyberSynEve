import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import './CSEAppCommon'
import {motion} from 'motion/react'
import React from 'react'
import { CSEAppStates } from './CSEAppCommon'

let [app_state, SetAppSate] = React.useState(CSEAppStates.STATE_INITIAL_CONNECT)
async function PingServer()
{
  try
  {
    
  }
  catch (err)
  {

  }
}

function App() 
{
  const [count, setCount] = React.useState(0)
  return (
    <>
      <div>
        <a href="https://vite.dev" target="_blank">
          <img src={viteLogo} className="logo" alt="Vite logo" />
        </a>
        <a href="https://react.dev" target="_blank">
          <img src={reactLogo} className="logo react" alt="React logo" />
        </a>
      </div>
      <h1>Vite + React</h1>
      <div className="card">
        <button onClick={() => setCount((count) => count + 1)}>
          count is {count}
        </button>
        <p>
          Edit <code>src/App.tsx</code> and save to test HMR
        </p>
      </div>
      <p className="read-the-docs">
        Click on the Vite and React logos to learn more
      </p>
    </>
  )
}

export default App

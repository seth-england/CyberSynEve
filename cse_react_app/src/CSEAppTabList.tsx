import * as CSEAppCommon from './CSEAppCommon'
import React from 'react'
import { CSEAppContext } from './CSEAppContext'
import type {CSEAppTab} from './CSEAppTab'
import type { CSEAppTabRequest } from './CSEAppTabRequest'
import CSEAppOpportunityView from './CSEAppOpportunityView'

interface CSEAppTabListInput
{
  m_ID: string,
}

function CSEAppTabList(props: CSEAppTabListInput)
{
  const [tab_list, set_tab_list] = React.useState(new Array<CSEAppTab>())
  const tab_requests = CSEAppContext((state) => state.m_TabRequests)
  const set_tab_requests = CSEAppContext((state) => state.m_SetTabRequests)

  function HandleTabRequest()
  {
    for (const tab_request of tab_requests)
    {
      if (tab_request.m_TargetListID === props.m_ID)
      {
        // Check that the tab request is not already in the tab list
        const existing_tab = tab_list.find((tab) => tab.m_Name === tab_request.m_Name)
        if (existing_tab)
        {
          // Remove the tab request from the tab requests array
          const new_tab_requests = tab_requests.filter((request) => request.m_Name !== tab_request.m_Name)
          set_tab_requests(new_tab_requests)
          return
        }

        const new_tab: CSEAppTab = {m_Name: tab_request.m_Name, m_ID: tab_request.m_ID, m_Element: <CSEAppOpportunityView m_CharacterID={tab_request.m_Prius} />}
        set_tab_list([...tab_list, new_tab])
      }
    }
  }

  React.useEffect(() => {HandleTabRequest()}, [tab_requests])

  function HandleTabClose(tab_id: string)
  {
    const new_tab_list = tab_list.filter((tab) => tab.m_ID !== tab_id)
    set_tab_list(new_tab_list)
  }

  const tab_names_jsx = tab_list.map(
    (tab) => 
    (
      <div 
        className='flex items-center justify-center bg-primary_bg border border-primary_border  shadow-sm hover:shadow-md hover:border-primary_accent transition-all duration-200 cursor-pointer group' 
        key={tab.m_ID}
      >
        <div className='text-sm px-2 font-medium text-primary_text group-hover:text-blue-600 transition-colors duration-200'>
          {tab.m_Name}
        </div>
        <div onClick={() => HandleTabClose(tab.m_ID)} className='flex text-center items-center justify-center text-xs h-full w-4 border border-primary_border text-primary_text hover:text-warning opacity-0 group-hover:opacity-100 transition-all duration-200'>
          x
        </div>
      </div>
    )
  )

  const tab_dividing_line_jsx = <div className='w-full bg-primary_accent h-1' />

  return (
    <div>
      <div className='flex flex-row w-full h-8'>
        {tab_names_jsx}
      </div>
      {tab_list.length > 0 ? tab_dividing_line_jsx : null}
    </div>
  )
}

export default CSEAppTabList
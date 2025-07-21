import * as CSEAppCommon from './CSEAppCommon'
import React from 'react'

function CSEAppCharacterCard({character_name, character_id}: any)
{
  return (
    <div className='flex border-primary_accent border-8'>
      {character_name}
    </div>
  )
}

export default CSEAppCharacterCard
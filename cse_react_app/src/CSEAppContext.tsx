import { createContext } from "react";

export class CSEAppContext
{
  m_Test = ""
}
export const cse_app_default_context = createContext(new CSEAppContext());

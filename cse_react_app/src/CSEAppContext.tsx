import { createContext } from "react";
import { CSEAppDefaultColorPalette } from './CSEAppColorPalette';

export class CSEAppContext
{
  m_ColorPalette = CSEAppDefaultColorPalette
}
export const cse_app_default_context = createContext(new CSEAppContext());

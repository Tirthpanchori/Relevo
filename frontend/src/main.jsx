import React from 'react';
import { createRoot } from 'react-dom/client';
import { MotionConfig } from 'motion/react';
import '@fontsource/instrument-sans/latin-400.css';
import '@fontsource/instrument-sans/latin-500.css';
import '@fontsource/instrument-sans/latin-600.css';
import '@fontsource/instrument-sans/latin-700.css';
import '@fontsource/ibm-plex-mono/latin-400.css';
import App from './App.jsx';
import './styles.css';
import './desktop.css';

createRoot(document.getElementById('root')).render(<React.StrictMode><MotionConfig reducedMotion="user"><App/></MotionConfig></React.StrictMode>);

import './responsive.css';

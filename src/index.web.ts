// Web entry point

import React from 'react';
import { AppRegistry } from 'react-native';
import App from '../App';
import { FirebaseService } from './services/firebase';

// Declare DOM types for web
declare global {
  interface Window {
    __INITIAL_STATE__: any;
  }
}

// Ensure Firebase is initialized before rendering the app
const SuperPasswordApp = () => {
  // Firebase is already initialized via the platform-specific import
  // This component just wraps the main App component
  return React.createElement(App);
};

AppRegistry.registerComponent("SuperPassword", () => SuperPasswordApp);
AppRegistry.runApplication("SuperPassword", {
  rootTag: document.getElementById("root"),
  initialProps: {},
});

// Handle web-specific setup
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker
      .register("/service-worker.js")
      .then((registration) => {
        console.log("SW registered:", registration);
      })
      .catch((error) => {
        console.log("SW registration failed:", error);
      });
  });
}

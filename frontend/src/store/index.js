//import { createStore } from 'vuex';

import Vuex from 'vuex';
// store/index.js
export default new Vuex.Store({
  state: {
    isAuthenticated: !!localStorage.getItem('token')
  },
  mutations: {
    setAuth(state, status) {
      state.isAuthenticated = status
    }
  }
})  

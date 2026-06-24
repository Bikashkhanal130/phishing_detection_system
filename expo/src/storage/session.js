import AsyncStorage from '@react-native-async-storage/async-storage';

const KEYS = { token: 'token', name: 'name', email: 'email' };

export default {
  save: (token, name, email) =>
    AsyncStorage.multiSet([
      [KEYS.token, token || ''],
      [KEYS.name, name || ''],
      [KEYS.email, email || ''],
    ]),

  getToken: () => AsyncStorage.getItem(KEYS.token),
  getName: () => AsyncStorage.getItem(KEYS.name),
  getEmail: () => AsyncStorage.getItem(KEYS.email),

  isLoggedIn: async () => !!(await AsyncStorage.getItem(KEYS.token)),

  logout: () => AsyncStorage.multiRemove(Object.values(KEYS)),
};

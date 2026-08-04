import React, { useState, useEffect, createContext } from 'react';
import { ActivityIndicator, View, Text, StyleSheet } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import session from './src/storage/session';
import LoginScreen from './src/screens/LoginScreen';
import RegisterScreen from './src/screens/RegisterScreen';
import OtpScreen from './src/screens/OtpScreen';
import ForgotPasswordScreen from './src/screens/ForgotPasswordScreen';
import ResetPasswordScreen from './src/screens/ResetPasswordScreen';
import HomeScreen from './src/screens/HomeScreen';
import HistoryScreen from './src/screens/HistoryScreen';
import ProfileScreen from './src/screens/ProfileScreen';

export const AuthContext = createContext(null);

const Stack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();

function MainTabs() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarActiveTintColor: '#1F6FEB',
        tabBarInactiveTintColor: '#6B7280',
        tabBarStyle: { backgroundColor: '#FFFFFF', borderTopColor: '#E2E8F0' },
        tabBarIcon: ({ color, size }) => {
          const icons = { Home: 'home', History: 'time', Profile: 'person' };
          return <Ionicons name={icons[route.name]} size={size} color={color} />;
        },
      })}
    >
      <Tab.Screen name="Home" component={HomeScreen} />
      <Tab.Screen name="History" component={HistoryScreen} />
      <Tab.Screen name="Profile" component={ProfileScreen} />
    </Tab.Navigator>
  );
}

export default function App() {
  const [loggedIn, setLoggedIn] = useState(null);

  useEffect(() => {
    let mounted = true;

    async function loadSession() {
      try {
        const value = await session.isLoggedIn();
        if (mounted) setLoggedIn(value);
      } catch (error) {
        if (mounted) setLoggedIn(false);
      }
    }

    loadSession();

    return () => {
      mounted = false;
    };
  }, []);

  if (loggedIn === null) {
    return (
      <View style={styles.splash}>
        <View style={styles.logoCircle}>
          <Text style={styles.logoEmoji}>🛡️</Text>
        </View>
        <Text style={styles.title}>Phishing Detector</Text>
        <Text style={styles.subtitle}>Checking your session…</Text>
        <ActivityIndicator size="large" color="#1F6FEB" style={{ marginTop: 16 }} />
      </View>
    );
  }

  return (
    <AuthContext.Provider value={{ setLoggedIn }}>
      <SafeAreaProvider>
        <StatusBar style="light" backgroundColor="#1F6FEB" />
        <NavigationContainer>
          <Stack.Navigator screenOptions={{ headerShown: false }}>
            {loggedIn ? (
              <Stack.Screen name="Main" component={MainTabs} />
            ) : (
              <>
                <Stack.Screen name="Login" component={LoginScreen} />
                <Stack.Screen name="Register" component={RegisterScreen} />
                <Stack.Screen name="OTP" component={OtpScreen} />
                <Stack.Screen name="ForgotPassword" component={ForgotPasswordScreen} />
                <Stack.Screen name="ResetPassword" component={ResetPasswordScreen} />
              </>
            )}
          </Stack.Navigator>
        </NavigationContainer>
      </SafeAreaProvider>
    </AuthContext.Provider>
  );
}

const styles = StyleSheet.create({
  splash: {
    flex: 1, justifyContent: 'center', alignItems: 'center',
    backgroundColor: '#F0F4FF', paddingHorizontal: 32,
  },
  logoCircle: {
    width: 84, height: 84, borderRadius: 42, backgroundColor: '#E1EBFF',
    justifyContent: 'center', alignItems: 'center', marginBottom: 16,
  },
  logoEmoji: { fontSize: 40 },
  title: { fontSize: 20, fontWeight: 'bold', color: '#111418', marginBottom: 6 },
  subtitle: { fontSize: 14, color: '#6B7280' },
});

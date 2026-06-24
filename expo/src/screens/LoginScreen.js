import React, { useState, useContext } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, StyleSheet,
  ActivityIndicator, Alert, ScrollView, KeyboardAvoidingView, Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import api from '../api/client';
import session from '../storage/session';
import { AuthContext } from '../../App';

const C = { primary: '#1F6FEB', bg: '#F0F4FF', surface: '#FFFFFF', text: '#111418', muted: '#6B7280', border: '#E2E8F0' };

export default function LoginScreen({ navigation }) {
  const { setLoggedIn } = useContext(AuthContext);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  async function doLogin() {
    if (!email.trim() || !password) { Alert.alert('Error', 'Enter email and password'); return; }
    setLoading(true);
    try {
      const { ok, status, data } = await api.login(email.trim().toLowerCase(), password);
      if (ok) {
        await session.save(data.token, data.user.full_name, data.user.email);
        setLoggedIn(true);
      } else if (status === 403 && data.need_verification) {
        navigation.navigate('OTP', { email: data.email || email.trim().toLowerCase() });
      } else {
        Alert.alert('Login failed', data.error || 'Wrong email or password');
      }
    } catch {
      Alert.alert('Error', 'Network error. Is the server running?');
    } finally {
      setLoading(false);
    }
  }

  return (
    <SafeAreaView style={s.safe}>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={{ flex: 1 }}>
        <ScrollView contentContainerStyle={s.container} keyboardShouldPersistTaps="handled">
          <Text style={s.emoji}>🛡️</Text>
          <Text style={s.title}>Phishing Detector</Text>
          <Text style={s.subtitle}>Check any link before you click</Text>

          <TextInput
            style={s.input} placeholder="Email" placeholderTextColor={C.muted}
            value={email} onChangeText={setEmail}
            keyboardType="email-address" autoCapitalize="none" autoCorrect={false}
          />
          <TextInput
            style={s.input} placeholder="Password" placeholderTextColor={C.muted}
            value={password} onChangeText={setPassword} secureTextEntry
          />

          <TouchableOpacity style={s.btn} onPress={doLogin} disabled={loading}>
            {loading ? <ActivityIndicator color="#fff" /> : <Text style={s.btnText}>Login</Text>}
          </TouchableOpacity>

          <TouchableOpacity style={s.link} onPress={() => navigation.navigate('Register')}>
            <Text style={s.linkText}>Create a new account</Text>
          </TouchableOpacity>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  safe: { flex: 1, backgroundColor: C.bg },
  container: { flexGrow: 1, justifyContent: 'center', padding: 24 },
  emoji: { textAlign: 'center', fontSize: 56, marginBottom: 8 },
  title: { textAlign: 'center', fontSize: 26, fontWeight: 'bold', color: C.text, marginBottom: 4 },
  subtitle: { textAlign: 'center', color: C.muted, marginBottom: 32, fontSize: 14 },
  input: {
    backgroundColor: C.surface, borderWidth: 1, borderColor: C.border, borderRadius: 10,
    paddingHorizontal: 14, paddingVertical: 12, fontSize: 15, color: C.text, marginBottom: 12,
  },
  btn: { backgroundColor: C.primary, borderRadius: 10, paddingVertical: 14, alignItems: 'center', marginTop: 4, marginBottom: 12 },
  btnText: { color: '#fff', fontWeight: 'bold', fontSize: 15 },
  link: { alignItems: 'center', paddingVertical: 10 },
  linkText: { color: C.primary, fontSize: 14 },
});

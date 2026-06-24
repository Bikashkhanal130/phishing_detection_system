import React, { useState } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, StyleSheet,
  ActivityIndicator, Alert, ScrollView, KeyboardAvoidingView, Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import api from '../api/client';

const C = { primary: '#1F6FEB', bg: '#F0F4FF', surface: '#FFFFFF', text: '#111418', muted: '#6B7280', border: '#E2E8F0' };

export default function RegisterScreen({ navigation }) {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  async function doRegister() {
    if (!name.trim() || !email.trim() || !password) { Alert.alert('Error', 'All fields are required'); return; }
    if (password.length < 6) { Alert.alert('Error', 'Password must be at least 6 characters'); return; }
    setLoading(true);
    try {
      const { ok, data } = await api.register(name.trim(), email.trim().toLowerCase(), password);
      if (ok) {
        navigation.navigate('OTP', { email: email.trim().toLowerCase() });
      } else {
        Alert.alert('Registration failed', data.error || 'Please try again');
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
          <Text style={s.title}>Create Account</Text>
          <Text style={s.subtitle}>Join Phishing Detector</Text>

          <TextInput style={s.input} placeholder="Full Name" placeholderTextColor={C.muted} value={name} onChangeText={setName} />
          <TextInput style={s.input} placeholder="Email" placeholderTextColor={C.muted} value={email} onChangeText={setEmail} keyboardType="email-address" autoCapitalize="none" autoCorrect={false} />
          <TextInput style={s.input} placeholder="Password (min 6 characters)" placeholderTextColor={C.muted} value={password} onChangeText={setPassword} secureTextEntry />

          <TouchableOpacity style={s.btn} onPress={doRegister} disabled={loading}>
            {loading ? <ActivityIndicator color="#fff" /> : <Text style={s.btnText}>Create Account</Text>}
          </TouchableOpacity>

          <TouchableOpacity style={s.link} onPress={() => navigation.goBack()}>
            <Text style={s.linkText}>Already have an account? Login</Text>
          </TouchableOpacity>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  safe: { flex: 1, backgroundColor: C.bg },
  container: { flexGrow: 1, justifyContent: 'center', padding: 24 },
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

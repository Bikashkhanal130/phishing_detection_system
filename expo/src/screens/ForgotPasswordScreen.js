import React, { useState } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, StyleSheet,
  ActivityIndicator, Alert, ScrollView, KeyboardAvoidingView, Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import api from '../api/client';

const C = { primary: '#1F6FEB', bg: '#F0F4FF', surface: '#FFFFFF', text: '#111418', muted: '#6B7280', border: '#E2E8F0' };

export default function ForgotPasswordScreen({ navigation }) {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);

  async function sendCode() {
    const trimmed = email.trim().toLowerCase();
    if (!trimmed) { Alert.alert('Error', 'Enter your account email'); return; }
    setLoading(true);
    try {
      const { ok, data } = await api.forgotPassword(trimmed);
      if (ok) {
        navigation.navigate('ResetPassword', { email: trimmed });
      } else {
        Alert.alert('Error', data.error || 'Could not send reset code');
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
          <Text style={s.emoji}>🔑</Text>
          <Text style={s.title}>Forgot Password</Text>
          <Text style={s.subtitle}>Enter your account email and we'll send you a code to reset your password</Text>

          <TextInput
            style={s.input} placeholder="Email" placeholderTextColor={C.muted}
            value={email} onChangeText={setEmail}
            keyboardType="email-address" autoCapitalize="none" autoCorrect={false}
          />

          <TouchableOpacity style={s.btn} onPress={sendCode} disabled={loading}>
            {loading ? <ActivityIndicator color="#fff" /> : <Text style={s.btnText}>Send Reset Code</Text>}
          </TouchableOpacity>

          <TouchableOpacity style={s.link} onPress={() => navigation.goBack()}>
            <Text style={s.linkText}>Back to Login</Text>
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
  subtitle: { textAlign: 'center', color: C.muted, marginBottom: 32, fontSize: 14, lineHeight: 20, paddingHorizontal: 8 },
  input: {
    backgroundColor: C.surface, borderWidth: 1, borderColor: C.border, borderRadius: 10,
    paddingHorizontal: 14, paddingVertical: 12, fontSize: 15, color: C.text, marginBottom: 12,
  },
  btn: { backgroundColor: C.primary, borderRadius: 10, paddingVertical: 14, alignItems: 'center', marginTop: 4, marginBottom: 12 },
  btnText: { color: '#fff', fontWeight: 'bold', fontSize: 15 },
  link: { alignItems: 'center', paddingVertical: 10 },
  linkText: { color: C.primary, fontSize: 14 },
});

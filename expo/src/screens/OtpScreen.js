import React, { useState, useContext } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, StyleSheet,
  ActivityIndicator, Alert, KeyboardAvoidingView, Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import api from '../api/client';
import session from '../storage/session';
import { AuthContext } from '../../App';

const C = { primary: '#1F6FEB', bg: '#F0F4FF', surface: '#FFFFFF', text: '#111418', muted: '#6B7280', border: '#E2E8F0' };

export default function OtpScreen({ route, navigation }) {
  const { setLoggedIn } = useContext(AuthContext);
  const { email } = route.params;
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);

  async function doVerify() {
    if (!code.trim()) { Alert.alert('Error', 'Enter the OTP code'); return; }
    setLoading(true);
    try {
      const { ok, data } = await api.verifyOtp(email, code.trim());
      if (ok) {
        await session.save(data.token, data.user.full_name, data.user.email);
        setLoggedIn(true);
      } else {
        Alert.alert('Error', data.error || 'Invalid or expired code');
      }
    } catch {
      Alert.alert('Error', 'Network error');
    } finally {
      setLoading(false);
    }
  }

  async function resend() {
    setResending(true);
    try {
      const { ok, data } = await api.resendOtp(email);
      Alert.alert(ok ? 'Sent' : 'Error', ok ? 'New code sent to your email' : (data.error || 'Failed'));
    } catch {
      Alert.alert('Error', 'Network error');
    } finally {
      setResending(false);
    }
  }

  return (
    <SafeAreaView style={s.safe}>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={{ flex: 1 }}>
        <View style={s.container}>
          <Text style={s.title}>Verify Email</Text>
          <Text style={s.subtitle}>Enter the 6-digit code sent to{'\n'}{email}</Text>

          <TextInput
            style={s.input} placeholder="000000" placeholderTextColor={C.muted}
            value={code} onChangeText={setCode}
            keyboardType="number-pad" maxLength={6} textAlign="center"
          />

          <TouchableOpacity style={s.btn} onPress={doVerify} disabled={loading}>
            {loading ? <ActivityIndicator color="#fff" /> : <Text style={s.btnText}>Verify</Text>}
          </TouchableOpacity>

          <TouchableOpacity style={s.link} onPress={resend} disabled={resending}>
            <Text style={s.linkText}>{resending ? 'Sending...' : "Didn't get a code? Resend"}</Text>
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  safe: { flex: 1, backgroundColor: C.bg },
  container: { flex: 1, justifyContent: 'center', padding: 24 },
  title: { textAlign: 'center', fontSize: 26, fontWeight: 'bold', color: C.text, marginBottom: 8 },
  subtitle: { textAlign: 'center', color: C.muted, marginBottom: 32, lineHeight: 22, fontSize: 14 },
  input: {
    backgroundColor: C.surface, borderWidth: 1, borderColor: C.border, borderRadius: 10,
    paddingVertical: 14, fontSize: 28, color: C.text, letterSpacing: 12, marginBottom: 16,
  },
  btn: { backgroundColor: C.primary, borderRadius: 10, paddingVertical: 14, alignItems: 'center', marginBottom: 12 },
  btnText: { color: '#fff', fontWeight: 'bold', fontSize: 15 },
  link: { alignItems: 'center', paddingVertical: 10 },
  linkText: { color: C.primary, fontSize: 14 },
});

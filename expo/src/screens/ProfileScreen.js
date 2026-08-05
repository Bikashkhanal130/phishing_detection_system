import React, { useState, useEffect, useContext } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, StyleSheet,
  ActivityIndicator, Alert, ScrollView, Image,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import * as ImagePicker from 'expo-image-picker';
import api, { BASE_URL } from '../api/client';
import session from '../storage/session';
import { AuthContext } from '../../App';

const C = {
  primary: '#1F6FEB', bg: '#F0F4FF', surface: '#FFFFFF',
  text: '#111418', muted: '#6B7280', border: '#E2E8F0', danger: '#C0392B',
};

export default function ProfileScreen() {
  const { setLoggedIn } = useContext(AuthContext);
  const [profile, setProfile] = useState({ full_name: '', email: '', phone: '', bio: '', profile_image: null });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => { loadProfile(); }, []);

  async function loadProfile() {
    setLoading(true);
    try {
      const token = await session.getToken();
      const { ok, data } = await api.getProfile(token);
      if (ok && data.user) setProfile(data.user);
    } catch {}
    finally { setLoading(false); }
  }

  async function saveProfile() {
    setSaving(true);
    try {
      const token = await session.getToken();
      const { ok, data } = await api.updateProfile(
        { full_name: profile.full_name, phone: profile.phone, bio: profile.bio },
        token,
      );
      if (ok) {
        await session.save(token, profile.full_name, profile.email);
        Alert.alert('Saved', 'Profile updated');
      } else {
        Alert.alert('Error', data.error || 'Update failed');
      }
    } catch {
      Alert.alert('Error', 'Network error');
    } finally {
      setSaving(false);
    }
  }

  async function pickImage() {
    const { granted } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!granted) {
      Alert.alert('Permission needed', 'Allow photo access to change your profile picture');
      return;
    }
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true, aspect: [1, 1], quality: 0.8,
    });
    if (!result.canceled && result.assets?.length > 0) {
      try {
        const token = await session.getToken();
        const { ok, data } = await api.uploadImage(result.assets[0].uri, token);
        if (ok) {
          setProfile(p => ({ ...p, profile_image: data.profile_image }));
          Alert.alert('Updated', 'Profile photo changed');
        } else {
          Alert.alert('Error', data.error || 'Upload failed');
        }
      } catch {
        Alert.alert('Error', 'Upload failed');
      }
    }
  }

  function logout() {
    Alert.alert('Log out', 'Are you sure?', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Log out', style: 'destructive', onPress: async () => {
        await session.logout();
        setLoggedIn(false);
      }},
    ]);
  }

  function set(key) { return v => setProfile(p => ({ ...p, [key]: v })); }

  if (loading) {
    return (
      <SafeAreaView style={s.safe}>
        <View style={s.header}><Text style={s.headerTitle}>My Profile</Text></View>
        <ActivityIndicator style={{ flex: 1 }} color={C.primary} size="large" />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={s.safe}>
      <View style={s.header}><Text style={s.headerTitle}>My Profile</Text></View>
      <ScrollView contentContainerStyle={s.content}>

        {/* Avatar card */}
        <View style={s.avatarCard}>
          <TouchableOpacity onPress={pickImage} style={s.avatarWrap}>
            {profile.profile_image ? (
              <Image
                source={{ uri: `${BASE_URL}/uploads/${profile.profile_image}` }}
                style={s.avatarImg}
                resizeMode="cover"
              />
            ) : (
              <View style={[s.avatarImg, s.avatarFallback]}>
                <Text style={s.avatarLetter}>{profile.full_name?.[0]?.toUpperCase() || 'U'}</Text>
              </View>
            )}
          </TouchableOpacity>
          <TouchableOpacity style={s.changeBtn} onPress={pickImage}>
            <Text style={s.changeBtnText}>Change Photo</Text>
          </TouchableOpacity>
        </View>

        {/* Details card */}
        <View style={s.card}>
          <Text style={s.cardTitle}>Account Details</Text>

          <Text style={s.label}>Full Name</Text>
          <TextInput style={s.input} value={profile.full_name || ''} onChangeText={set('full_name')} placeholderTextColor={C.muted} />

          <Text style={s.label}>Email</Text>
          <TextInput style={[s.input, s.inputDisabled]} value={profile.email || ''} editable={false} placeholderTextColor={C.muted} />

          <Text style={s.label}>Phone</Text>
          <TextInput style={s.input} value={profile.phone || ''} onChangeText={set('phone')} keyboardType="phone-pad" placeholderTextColor={C.muted} />

          <Text style={s.label}>Bio</Text>
          <TextInput style={[s.input, s.multiline]} value={profile.bio || ''} onChangeText={set('bio')} multiline numberOfLines={3} placeholderTextColor={C.muted} textAlignVertical="top" />

          <TouchableOpacity style={s.saveBtn} onPress={saveProfile} disabled={saving}>
            {saving ? <ActivityIndicator color="#fff" /> : <Text style={s.saveBtnText}>Save Profile</Text>}
          </TouchableOpacity>
        </View>

        {/* Logout */}
        <TouchableOpacity style={s.logoutBtn} onPress={logout}>
          <Text style={s.logoutText}>Log Out</Text>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  safe: { flex: 1, backgroundColor: C.bg },
  header: { backgroundColor: C.primary, paddingHorizontal: 16, paddingVertical: 14 },
  headerTitle: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
  content: { padding: 12, paddingBottom: 40 },
  avatarCard: {
    backgroundColor: C.primary, borderRadius: 16, padding: 20,
    alignItems: 'center', marginBottom: 10,
  },
  avatarWrap: { marginBottom: 10 },
  avatarImg: { width: 80, height: 80, borderRadius: 40 },
  avatarFallback: { backgroundColor: 'rgba(255,255,255,0.25)', justifyContent: 'center', alignItems: 'center' },
  avatarLetter: { color: '#fff', fontSize: 32, fontWeight: 'bold' },
  changeBtn: { borderWidth: 1, borderColor: 'rgba(255,255,255,0.6)', borderRadius: 8, paddingHorizontal: 14, paddingVertical: 5 },
  changeBtnText: { color: '#fff', fontSize: 12 },
  card: {
    backgroundColor: C.surface, borderRadius: 16, padding: 14, marginBottom: 10,
    shadowColor: '#000', shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.08, shadowRadius: 3, elevation: 2,
  },
  cardTitle: { fontWeight: 'bold', fontSize: 14, color: C.text, marginBottom: 10 },
  label: { fontSize: 12, color: C.muted, marginBottom: 4, marginTop: 6 },
  input: {
    borderWidth: 1, borderColor: C.border, borderRadius: 10,
    paddingHorizontal: 12, paddingVertical: 10, fontSize: 14, color: C.text,
  },
  inputDisabled: { backgroundColor: '#F5F5F5', color: C.muted },
  multiline: { height: 80 },
  saveBtn: { backgroundColor: C.primary, borderRadius: 10, paddingVertical: 12, alignItems: 'center', marginTop: 14 },
  saveBtnText: { color: '#fff', fontWeight: 'bold', fontSize: 14 },
  logoutBtn: { borderWidth: 1.5, borderColor: C.danger, borderRadius: 12, paddingVertical: 12, alignItems: 'center' },
  logoutText: { color: C.danger, fontWeight: 'bold', fontSize: 14 },
});

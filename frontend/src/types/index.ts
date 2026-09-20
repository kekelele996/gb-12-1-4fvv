export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: 'student' | 'consultant' | 'admin';
  role_display: string;
  phone: string;
  bio: string;
  date_joined: string;
  get_full_name?: string;
  student_profile?: StudentProfile;
  consultant_profile?: ConsultantProfile;
}

export interface StudentProfile {
  id: number;
  user: User;
  target_country: string;
  target_degree: string;
  gpa: number | null;
  ielts_score: number | null;
  toefl_score: number | null;
  gre_score: number | null;
  gmat_score: number | null;
  consultant: number | null;
  consultant_name: string | null;
  bio?: string;
  created_at: string;
  updated_at: string;
}

export interface ConsultantProfile {
  id: number;
  user: User;
  specialization: string;
  experience_years: number;
  success_cases: number;
  students_count: number;
  bio?: string;
  created_at: string;
  updated_at: string;
}

export interface University {
  id: number;
  name: string;
  country: string;
  city: string;
  qs_ranking: number | null;
  times_ranking: number | null;
  description: string;
  logo: string | null;
  website: string;
  tuition_min: number | null;
  tuition_max: number | null;
  tuition_currency: string;
  programs_count: number;
  created_at: string;
  updated_at: string;
}

export interface Program {
  id: number;
  university: number;
  university_name: string;
  name: string;
  degree_level: 'bachelor' | 'master' | 'phd';
  degree_level_display: string;
  department: string;
  tuition: number | null;
}

export interface ApplicationProject {
  id: number;
  student: number;
  student_name: string;
  university: number;
  university_name: string;
  program: number;
  program_name: string;
  application_round: number | null;
  status: string;
  status_display: string;
  notes: string;
  application_fee: number | null;
  fee_paid: boolean;
  submitted_at: string | null;
  result_date: string | null;
  materials_progress: number;
  status_history: StatusChangeHistory[];
  created_at: string;
  updated_at: string;
}

export interface StatusChangeHistory {
  id: number;
  application: number;
  from_status: string | null;
  from_status_display: string | null;
  to_status: string;
  to_status_display: string;
  changed_by: number | null;
  changed_by_name: string | null;
  change_reason: string;
  created_at: string;
}

export interface Document {
  id: number;
  application: number;
  document_type: string;
  document_type_display: string;
  title: string;
  description: string;
  file: string | null;
  current_version: DocumentVersion | null;
  versions_count: number;
  comments_count: number;
  created_by: number | null;
  created_by_name: string | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentVersion {
  id: number;
  document: number;
  version_number: number;
  content: string;
  file: string | null;
  word_count: number;
  created_by: number | null;
  created_by_name: string | null;
  change_note: string;
  diff_from_previous: string;
  created_at: string;
}

export interface DocumentComment {
  id: number;
  document: number;
  version: number | null;
  author: number;
  author_name: string;
  content: string;
  start_position: number | null;
  end_position: number | null;
  highlighted_text: string;
  is_resolved: boolean;
  parent: number | null;
  replies: DocumentComment[];
  created_at: string;
  updated_at: string;
}

export interface MaterialItem {
  id: number;
  application: number;
  name: string;
  material_type: string;
  material_type_display: string;
  description: string;
  is_required: boolean;
  is_completed: boolean;
  file: string | null;
  uploaded_by: number | null;
  uploaded_by_name: string | null;
  uploaded_at: string | null;
  notes: string;
  created_at: string;
  updated_at: string;
}

export interface TimelineEvent {
  id: number;
  application: number;
  event_type: string;
  event_type_display: string;
  title: string;
  description: string;
  event_date: string;
  deadline_date: string | null;
  reminder_sent: boolean;
  is_completed: boolean;
  completed_at: string | null;
  created_by: number | null;
  created_by_name: string | null;
  created_at: string;
  updated_at: string;
}

export interface Notification {
  id: number;
  recipient: number;
  notification_type: string;
  notification_type_display: string;
  priority: string;
  priority_display: string;
  title: string;
  content: string;
  related_event: number | null;
  related_application: number | null;
  is_read: boolean;
  read_at: string | null;
  sent_at: string | null;
  created_at: string;
}

export interface Conversation {
  id: number;
  participants: number[];
  participant_names: string[];
  subject: string;
  related_application: number | null;
  last_message: Message | null;
  unread_count: number;
  last_message_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: number;
  conversation: number;
  sender: number;
  sender_name: string;
  content: string;
  is_read: boolean;
  read_at: string | null;
  attachments: MessageAttachment[];
  created_at: string;
}

export interface MessageAttachment {
  id: number;
  file: string;
  filename: string;
  created_at: string;
}

export interface DashboardData {
  total_applications: number;
  status_distribution: { status: string; count: number }[];
  admitted_count: number;
  rejected_count: number;
  submitted_count: number;
  acceptance_rate: number;
  countries_distribution: { university__country: string; count: number }[];
}

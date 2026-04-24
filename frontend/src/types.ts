export interface User {
  id: string;
  email: string;
  name: string;
  picture: string | null;
}

export interface DogMetadata {
  dog_name: string;
  breed: string;
  color: string;
  age: string;
  distinctive_markings: string;
  location: string;
  contact_email: string;
  lost_or_found: "lost" | "found";
  latitude?: number | null;
  longitude?: number | null;
}

export interface ReportResponse {
  dog_id: string;
}

export interface MatchResult {
  dog_id: string;
  similarity: number;
  metadata: DogMetadata;
  image: string | null;
  status?: "active" | "reunited";
}

export interface MatchResponse {
  matches: MatchResult[];
}

export interface DogDetailResponse {
  dog_id: string;
  chroma_id?: string;
  metadata: DogMetadata;
  image: string | null;
  images?: string[];
  status?: "active" | "reunited";
  latitude?: number | null;
  longitude?: number | null;
  created_at?: string;
}

export interface DogsListResponse {
  dogs: DogDetailResponse[];
}

export interface MessageThread {
  dog_id: string;
  dog_name: string;
  unread_count: number;
  latest_message: string;
  latest_at: string;
  sender_name: string;
}

export interface MessageItem {
  message_id: string;
  sender_id: string;
  sender_name: string;
  body: string;
  created_at: string;
  read: boolean;
  is_mine: boolean;
  is_system?: boolean;
}

export interface InboxResponse {
  threads: MessageThread[];
}

export interface ThreadResponse {
  messages: MessageItem[];
  dog_name: string;
}

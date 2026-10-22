import { request } from "@/api/client";

export type LoginResult = {
  access_token: string;
  token_type: "Bearer";
  expires_in: number;
  user: {
    id: string;
    account_name: string;
    display_name: string;
  };
};

export async function login(account_name: string, password: string): Promise<LoginResult> {
  return request<LoginResult>("/auth/login", {
    method: "POST",
    body: { account_name, password }
  });
}

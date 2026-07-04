enum Role { admin, gestor, coordenador, coletor, convidado }

Role roleFromWire(String value) => Role.values.firstWhere(
  (r) => r.name == value,
  orElse: () => throw ArgumentError('Papel desconhecido: $value'),
);

class AppUser {
  final String id;
  final String name;
  final String email;
  final Role role;
  final String organizationId;

  const AppUser({
    required this.id,
    required this.name,
    required this.email,
    required this.role,
    required this.organizationId,
  });

  factory AppUser.fromJson(Map<String, dynamic> json) => AppUser(
    id: json['id'] as String,
    name: json['name'] as String,
    email: json['email'] as String,
    role: roleFromWire(json['role'] as String),
    organizationId: json['organization_id'] as String,
  );

  Map<String, dynamic> toJson() => {
    'id': id,
    'name': name,
    'email': email,
    'role': role.name,
    'organization_id': organizationId,
  };
}

class Team {
  final String id;
  final String name;
  final String contractId;

  const Team({required this.id, required this.name, required this.contractId});

  factory Team.fromJson(Map<String, dynamic> json) =>
      Team(id: json['id'] as String, name: json['name'] as String, contractId: json['contract_id'] as String);
}

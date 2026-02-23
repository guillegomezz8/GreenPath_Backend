from rest_framework import serializers
from apps.route.models import Zone  # o donde esté definido tu modelo
from django.contrib.gis.geos import Polygon, GEOSException
import re
import logging

logger = logging.getLogger(__name__)

class ZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Zone
        fields = ['id', 'name', 'polygon']


class CreateZoneSerializer(serializers.Serializer):
    name = serializers.CharField(required=True)
    polygon = serializers.CharField(required=True)

    class Meta:
        fields = ['name', 'polygon']

    def to_internal_value(self, data):
        name = data.get("name")
        if not name:
            raise serializers.ValidationError({"name": "Este campo es obligatorio."})

        polygon_data = data.get("polygon")
        if not polygon_data:
            raise serializers.ValidationError({"polygon": "Este campo es obligatorio."})

        coords = self._parse_polygon_data(polygon_data)

        if len(coords) < 3:
            raise serializers.ValidationError({"polygon": "El polígono debe tener al menos 3 puntos."})

        if coords[0] != coords[-1]:
            coords.append(coords[0])

        if len(coords) < 4:
            raise serializers.ValidationError({"polygon": "El polígono cerrado debe tener al menos 4 puntos."})

        try:
            polygon_obj = Polygon(coords)
        except GEOSException as e:
            raise serializers.ValidationError({"polygon": f"Error al crear el polígono: {str(e)}"})

        validated_data = {"name": name, "polygon": polygon_obj}
        return validated_data

    def _parse_polygon_data(self, polygon_data):
        """
        Parsea los datos del polígono que pueden venir en diferentes formatos:
        1. String WKT: "POLYGON((lng lat, lng lat, ...))"
        2. Array de coordenadas: [[lng, lat], [lng, lat], ...]
        3. Formato anidado del frontend anterior: polygon[0][i][0], polygon[0][i][1]
        """
        coords = []

        if isinstance(polygon_data, str):
            coords = self._parse_wkt_string(polygon_data)
        elif isinstance(polygon_data, list):
            coords = self._parse_coordinates_array(polygon_data)
        else:
            raise serializers.ValidationError({"polygon": "Formato de polígono no válido."})

        return coords

    def _parse_wkt_string(self, wkt_string):
        try:
            match = re.search(r'POLYGON\s*\(\s*\((.*?)\)\s*\)', wkt_string, re.IGNORECASE)
            if not match:
                raise serializers.ValidationError({"polygon": "Formato WKT inválido."})
            
            coords_string = match.group(1)
            coords = []
            
            for coord_pair in coords_string.split(','):
                coord_pair = coord_pair.strip()
                if coord_pair:
                    parts = coord_pair.split()
                    if len(parts) != 2:
                        raise serializers.ValidationError({"polygon": f"Coordenada inválida: {coord_pair}"})
                    
                    try:
                        lng = float(parts[0])
                        lat = float(parts[1])
                        coords.append((lng, lat))
                    except ValueError:
                        raise serializers.ValidationError({"polygon": f"Coordenadas numéricas inválidas: {coord_pair}"})
            
            return coords
            
        except Exception as e:
            logger.error(f"[zone_serializers - _parse_wkt_string] Error parsing WKT string: {str(e)}")
            raise serializers.ValidationError({"polygon": f"Error al parsear coordenadas WKT: {str(e)}"})

    def _parse_coordinates_array(self, coords_array):
        coords = []
        try:
            for coord in coords_array:
                if len(coord) != 2:
                    raise serializers.ValidationError({"polygon": f"Coordenada debe tener exactamente 2 valores: {coord}"})
                
                lng = float(coord[0])
                lat = float(coord[1])
                coords.append((lng, lat))
            
            return coords
            
        except (ValueError, TypeError) as e:
            raise serializers.ValidationError({"polygon": f"Error al parsear array de coordenadas: {str(e)}"})

    def create(self, validated_data):
        try:
            return Zone.objects.create(**validated_data)
        except Exception as e:
            logger.error(f"[zone_serializers - create] Error al crear zona: {str(e)}")
            raise serializers.ValidationError(f"Error al crear zona: {str(e)}")


class UpdateZoneSerializer(serializers.Serializer):
    name = serializers.CharField(required=True)
    polygon = serializers.CharField(required=True)

    class Meta:
        fields = ['name', 'polygon']

    def to_internal_value(self, data):
        name = data.get("name")
        if not name:
            raise serializers.ValidationError({"name": "Este campo es obligatorio."})

        polygon_data = data.get("polygon")
        if not polygon_data:
            raise serializers.ValidationError({"polygon": "Este campo es obligatorio."})

        coords = self._parse_polygon_data(polygon_data)

        if len(coords) < 3:
            raise serializers.ValidationError({"polygon": "El polígono debe tener al menos 3 puntos."})

        if coords[0] != coords[-1]:
            coords.append(coords[0])

        if len(coords) < 4:
            raise serializers.ValidationError({"polygon": "El polígono cerrado debe tener al menos 4 puntos."})

        try:
            polygon_obj = Polygon(coords)
        except GEOSException as e:
            raise serializers.ValidationError({"polygon": f"Error al crear el polígono: {str(e)}"})

        validated_data = {"name": name, "polygon": polygon_obj}
        return validated_data

    def _parse_polygon_data(self, polygon_data):
        """
        Parsea los datos del polígono que pueden venir en diferentes formatos:
        1. String WKT: "POLYGON((lng lat, lng lat, ...))"
        2. Array de coordenadas: [[lng, lat], [lng, lat], ...]
        3. Formato anidado del frontend anterior: polygon[0][i][0], polygon[0][i][1]
        """
        coords = []

        if isinstance(polygon_data, str):
            coords = self._parse_wkt_string(polygon_data)
        elif isinstance(polygon_data, list):
            coords = self._parse_coordinates_array(polygon_data)
        else:
            raise serializers.ValidationError({"polygon": "Formato de polígono no válido."})

        return coords

    def _parse_wkt_string(self, wkt_string):
        try:
            match = re.search(r'POLYGON\s*\(\s*\((.*?)\)\s*\)', wkt_string, re.IGNORECASE)
            if not match:
                raise serializers.ValidationError({"polygon": "Formato WKT inválido."})
            
            coords_string = match.group(1)
            coords = []
            
            for coord_pair in coords_string.split(','):
                coord_pair = coord_pair.strip()
                if coord_pair:
                    parts = coord_pair.split()
                    if len(parts) != 2:
                        raise serializers.ValidationError({"polygon": f"Coordenada inválida: {coord_pair}"})
                    
                    try:
                        lng = float(parts[0])
                        lat = float(parts[1])
                        coords.append((lng, lat))
                    except ValueError:
                        raise serializers.ValidationError({"polygon": f"Coordenadas numéricas inválidas: {coord_pair}"})
            
            return coords
            
        except Exception as e:
            logger.error(f"[zone_serializers - _parse_wkt_string] Error parsing WKT string: {str(e)}")
            raise serializers.ValidationError({"polygon": f"Error al parsear coordenadas WKT: {str(e)}"})

    def _parse_coordinates_array(self, coords_array):
        coords = []
        try:
            for coord in coords_array:
                if len(coord) != 2:
                    raise serializers.ValidationError({"polygon": f"Coordenada debe tener exactamente 2 valores: {coord}"})
                
                lng = float(coord[0])
                lat = float(coord[1])
                coords.append((lng, lat))
            
            return coords
            
        except (ValueError, TypeError) as e:
            raise serializers.ValidationError({"polygon": f"Error al parsear array de coordenadas: {str(e)}"})

    def update(self, instance, validated_data):
        try:
            instance.name = validated_data.get("name", instance.name)
            instance.polygon = validated_data.get("polygon", instance.polygon)
            instance.save()
            return instance
        except Exception as e:
            logger.error(f"[zone_serializers - update] Error al actualizar zona {instance.id}: {str(e)}")
            raise serializers.ValidationError(f"Error al actualizar zona: {str(e)}")
